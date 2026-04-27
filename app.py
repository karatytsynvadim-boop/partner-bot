import asyncio
import json
import os
import threading
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from flask import Flask

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = "8768778011:AAGy_xl12xKhrGdZ6iVK28TS5w-OANuAlRM"
ADMIN_IDS = [284954186]
# =======================

# Flask приложение для healthcheck
app_flask = Flask(__name__)

@app_flask.route('/')
@app_flask.route('/health')
def health():
    return "Bot is running", 200

# Telegram бот
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

GROUPS_FILE = "groups.json"

def load_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}

def save_groups(groups):
    with open(GROUPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)

groups = load_groups()

class BroadcastState(StatesGroup):
    waiting_for_text = State()
    selecting_groups = State()

def main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="broadcast")],
        [InlineKeyboardButton(text="📋 Список групп", callback_data="list")],
        [InlineKeyboardButton(text="➕ Добавить эту группу", callback_data="add_here")],
        [InlineKeyboardButton(text="➖ Удалить эту группу", callback_data="remove_here")]
    ])
    return keyboard

def groups_keyboard(groups_dict, selected=None):
    if selected is None:
        selected = set()
    
    buttons = []
    for chat_id, title in groups_dict.items():
        short_title = title[:25] + "..." if len(title) > 25 else title
        check = "✅ " if chat_id in selected else "⬜ "
        buttons.append([InlineKeyboardButton(
            text=f"{check}{short_title}",
            callback_data=f"toggle_{chat_id}"
        )])
    
    buttons.append([
        InlineKeyboardButton(text="✅ Выбрать все", callback_data="select_all"),
        InlineKeyboardButton(text="❌ Очистить все", callback_data="clear_all")
    ])
    buttons.append([
        InlineKeyboardButton(text="📤 Отправить", callback_data="send"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def is_admin(user_id):
    return user_id in ADMIN_IDS

@dp.message(Command("start"))
async def start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    
    await message.answer(
        "🤝 *Помощник координатора*\n\n"
        "📌 *Как добавить группу:*\n"
        "1. Добавь бота в группу и дай права админа\n"
        "2. В группе напиши /start и нажми «Добавить эту группу»\n\n"
        "📢 Для рассылки нажми «Сделать рассылку»\n\n"
        "⚡ *Команды:*\n"
        "/add - добавить текущую группу\n"
        "/remove - удалить текущую группу\n"
        "/groups - список групп\n"
        "/cancel - отменить рассылку",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.message(Command("add"))
async def add_group(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("❌ Эта команда работает только в группах")
        return
    
    chat_id = message.chat.id
    title = message.chat.title
    
    try:
        member = await bot.get_chat_member(chat_id, bot.id)
        if member.status not in ["administrator", "creator"]:
            await message.answer("❌ Бот не является администратором! Добавь бота в админы.")
            return
    except:
        await message.answer("❌ Ошибка доступа. Убедись, что бот добавлен в группу.")
        return
    
    groups[chat_id] = title
    save_groups(groups)
    await message.answer(f"✅ Группа «{title}» добавлена в список рассылки!")

@dp.message(Command("remove"))
async def remove_group(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("❌ Эта команда работает только в группах")
        return
    
    chat_id = message.chat.id
    if chat_id in groups:
        title = groups[chat_id]
        del groups[chat_id]
        save_groups(groups)
        await message.answer(f"✅ Группа «{title}» удалена из списка")
    else:
        await message.answer("❌ Эта группа не в списке рассылки")

@dp.message(Command("groups"))
async def show_groups(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    if not groups:
        await message.answer("📭 Список групп пуст. Добавь группы через /add")
    else:
        text = "📋 *Список групп:*\n\n"
        for title in groups.values():
            text += f"• {title}\n"
        await message.answer(text, parse_mode="Markdown")

@dp.callback_query(F.data == "broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    
    if not groups:
        await callback.message.edit_text("📭 Нет групп! Добавь группы через /add", reply_markup=main_menu())
        await callback.answer()
        return
    
    await state.set_state(BroadcastState.waiting_for_text)
    await callback.message.edit_text(
        "✍️ *Напиши текст рассылки*\n\n"
        "Текст можно форматировать:\n"
        "• <b>жирный</b>\n"
        "• <i>курсив</i>\n"
        "• <u>подчеркнутый</u>\n\n"
        "Отправь /cancel для отмены",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(BroadcastState.waiting_for_text)
async def get_broadcast_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.update_data(text=message.text)
    await state.set_state(BroadcastState.selecting_groups)
    
    await message.answer(
        "🎯 *Выбери группы для рассылки:*\n\n"
        "✅ - группа выбрана\n"
        "⬜ - группа не выбрана",
        parse_mode="Markdown",
        reply_markup=groups_keyboard(groups)
    )

@dp.callback_query(BroadcastState.selecting_groups)
async def select_groups(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = set(data.get("selected", []))
    
    if callback.data == "select_all":
        selected = set(groups.keys())
        await callback.answer("✅ Выбраны все группы")
    
    elif callback.data == "clear_all":
        selected.clear()
        await callback.answer("❌ Все группы очищены")
    
    elif callback.data == "send":
        if not selected:
            await callback.answer("❌ Выбери хотя бы одну группу!", show_alert=True)
            return
        
        text = data.get("text")
        await state.update_data(selected=list(selected))
        
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, отправить", callback_data="confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ])
        
        await callback.message.edit_text(
            f"📢 *Подтверждение рассылки*\n\n"
            f"Текст:\n{text[:200]}{'...' if len(text) > 200 else ''}\n\n"
            f"📊 Получателей: {len(selected)} групп\n\n"
            f"Отправить?",
            parse_mode="Markdown",
            reply_markup=confirm_keyboard
        )
        return
    
    elif callback.data == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Рассылка отменена", reply_markup=main_menu())
        await callback.answer()
        return
    
    elif callback.data.startswith("toggle_"):
        chat_id = int(callback.data.split("_")[1])
        if chat_id in selected:
            selected.remove(chat_id)
            await callback.answer("❌ Группа убрана")
        else:
            selected.add(chat_id)
            await callback.answer("✅ Группа добавлена")
    
    await state.update_data(selected=list(selected))
    await callback.message.edit_reply_markup(
        reply_markup=groups_keyboard(groups, selected)
    )

@dp.callback_query(F.data == "confirm")
async def send_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data.get("text")
    selected = data.get("selected", [])
    
    await callback.message.edit_text("🚀 *Отправляю рассылку...*", parse_mode="Markdown")
    
    success = 0
    fail = 0
    fail_titles = []
    
    for chat_id in selected:
        try:
            await bot.send_message(chat_id, text, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            fail += 1
            fail_titles.append(groups.get(chat_id, str(chat_id)))
    
    result_text = f"✅ *Рассылка завершена!*\n\n📤 Успешно: {success}\n❌ Ошибок: {fail}"
    
    if fail_titles:
        result_text += f"\n\n⚠️ Ошибки в группах:\n" + "\n".join(f"• {t}" for t in fail_titles[:5])
    
    await callback.message.edit_text(result_text, parse_mode="Markdown")
    await callback.message.answer("🔙 Вернуться в меню", reply_markup=main_menu())
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "list")
async def list_groups(callback: CallbackQuery):
    if not groups:
        text = "📭 Групп пока нет"
    else:
        text = "📋 *Список групп:*\n\n" + "\n".join(f"• {title}" for title in groups.values())
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())
    await callback.answer()

@dp.callback_query(F.data == "add_here")
async def add_here(callback: CallbackQuery):
    await callback.answer("Напиши /add в группе, где хочешь добавить бота", show_alert=True)

@dp.callback_query(F.data == "remove_here")
async def remove_here(callback: CallbackQuery):
    await callback.answer("Напиши /remove в группе, которую хочешь удалить", show_alert=True)

@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено", reply_markup=main_menu())

# Функция для запуска бота в фоне
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dp.start_polling(bot))

# Запускаем бота в отдельном потоке при импорте модуля
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

print("✅ Flask и бот запущены")