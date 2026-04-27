import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ========== НАСТРОЙКИ (изменяйте только здесь) ==========
BOT_TOKEN = "8768778011:AAGy_xl12xKhrGdZ6iVK28TS5w-OANuAlRM"
SUPER_ADMINS = [284954186]          # ID тех, кто может назначать других админов
# ========================================================

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# файлы для хранения данных
GROUPS_FILE = "groups.json"
ADMINS_FILE = "admins.json"

# --- работа с группами ---
def load_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()} if isinstance(data, dict) else {}
    return {}

def save_groups(groups):
    with open(GROUPS_FILE, 'w', encoding='utf-8') as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)

groups = load_groups()

# --- работа со списком админов (кроме суперадминов) ---
def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    return []

def save_admins(admins):
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(admins, f, ensure_ascii=False, indent=2)

extra_admins = load_admins()

def is_admin(user_id: int) -> bool:
    return user_id in SUPER_ADMINS or user_id in extra_admins

# --- состояния для рассылки ---
class BroadcastState(StatesGroup):
    waiting_for_text = State()
    selecting_groups = State()

# --- клавиатуры ---
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="broadcast")],
        [InlineKeyboardButton(text="📋 Список групп", callback_data="list_groups")],
        [InlineKeyboardButton(text="➕ Добавить эту группу", callback_data="add_here")],
        [InlineKeyboardButton(text="➖ Удалить эту группу", callback_data="remove_here")]
    ])

def groups_keyboard(groups_dict, selected=None):
    selected = selected or set()
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
        InlineKeyboardButton(text="📤 Отправить", callback_data="send_broadcast"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- команды для всех админов ---
@dp.message(Command("start"))
async def start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этому боту.")
        return
    await message.answer(
        "🤝 *Помощник координатора*\n\n"
        "📌 *Как добавить группу:*\n"
        "1. Добавьте бота в группу и дайте права администратора.\n"
        "2. В группе напишите /add — бот запомнит группу.\n\n"
        "📢 *Рассылка:* нажмите «Сделать рассылку» в меню.\n\n"
        "⚡ *Команды для админов:*\n"
        "/add — добавить текущую группу\n"
        "/remove — удалить текущую группу\n"
        "/groups — список всех групп\n\n"
        "👑 *Команды суперадмина:*\n"
        "/add_admin <ID> — добавить администратора\n"
        "/remove_admin <ID> — удалить администратора\n"
        "/list_admins — список администраторов",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

@dp.message(Command("add"))
async def add_group(message: Message):
    if not is_admin(message.from_user.id):
        return
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("❌ Эта команда работает только в группах.")
        return
    chat_id = message.chat.id
    title = message.chat.title
    try:
        member = await bot.get_chat_member(chat_id, bot.id)
        if member.status not in ["administrator", "creator"]:
            await message.answer("❌ Бот не администратор! Дайте ему права администратора.")
            return
    except:
        await message.answer("❌ Ошибка доступа. Убедитесь, что бот добавлен в группу.")
        return
    groups[chat_id] = title
    save_groups(groups)
    await message.answer(f"✅ Группа «{title}» добавлена в список рассылки.")

@dp.message(Command("remove"))
async def remove_group(message: Message):
    if not is_admin(message.from_user.id):
        return
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("❌ Команда работает только в группах.")
        return
    chat_id = message.chat.id
    if chat_id in groups:
        title = groups.pop(chat_id)
        save_groups(groups)
        await message.answer(f"✅ Группа «{title}» удалена из списка.")
    else:
        await message.answer("❌ Эта группа не в списке.")

@dp.message(Command("groups"))
async def list_groups_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    if not groups:
        await message.answer("📭 Список групп пуст.")
    else:
        text = "📋 *Список групп:*\n\n" + "\n".join(f"• {title}" for title in groups.values())
        await message.answer(text, parse_mode="Markdown")

# --- команды суперадмина для управления админами ---
@dp.message(Command("add_admin"))
async def add_admin_command(message: Message):
    if message.from_user.id not in SUPER_ADMINS:
        await message.answer("⛔ Только суперадмин может добавлять администраторов.")
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Формат: `/add_admin <числовой ID>`", parse_mode="Markdown")
        return
    try:
        new_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return
    if new_id in SUPER_ADMINS:
        await message.answer("⚠️ Этот пользователь уже суперадмин.")
        return
    if new_id in extra_admins:
        await message.answer("⚠️ Пользователь уже в списке администраторов.")
        return
    extra_admins.append(new_id)
    save_admins(extra_admins)
    await message.answer(f"✅ Пользователь с ID `{new_id}` добавлен в администраторы.", parse_mode="Markdown")

@dp.message(Command("remove_admin"))
async def remove_admin_command(message: Message):
    if message.from_user.id not in SUPER_ADMINS:
        await message.answer("⛔ Только суперадмин может удалять администраторов.")
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Формат: `/remove_admin <числовой ID>`", parse_mode="Markdown")
        return
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return
    if user_id in SUPER_ADMINS:
        await message.answer("⚠️ Нельзя удалить суперадмина через эту команду.")
        return
    if user_id in extra_admins:
        extra_admins.remove(user_id)
        save_admins(extra_admins)
        await message.answer(f"✅ Пользователь с ID `{user_id}` удалён из администраторов.", parse_mode="Markdown")
    else:
        await message.answer("❌ Такого администратора нет в списке.")

@dp.message(Command("list_admins"))
async def list_admins_command(message: Message):
    if message.from_user.id not in SUPER_ADMINS:
        await message.answer("⛔ Только суперадмин может видеть список администраторов.")
        return
    text = "👑 *Суперадмины:*\n" + "\n".join(f"• `{uid}`" for uid in SUPER_ADMINS)
    if extra_admins:
        text += "\n\n👥 *Обычные администраторы:*\n" + "\n".join(f"• `{uid}`" for uid in extra_admins)
    else:
        text += "\n\n👥 Обычных администраторов нет."
    await message.answer(text, parse_mode="Markdown")

# --- рассылка (доступна всем админам) ---
@dp.callback_query(F.data == "broadcast")
async def start_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    if not groups:
        await callback.message.edit_text("📭 Нет добавленных групп.", reply_markup=main_menu())
        await callback.answer()
        return
    await state.set_state(BroadcastState.waiting_for_text)
    await callback.message.edit_text(
        "✍️ *Напишите текст рассылки*\n\nМожно использовать HTML-разметку: <b>жирный</b>, <i>курсив</i>.\n"
        "Отправьте /cancel для отмены.",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(BroadcastState.waiting_for_text)
async def receive_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(text=message.text_html or message.text)
    await state.set_state(BroadcastState.selecting_groups)
    await message.answer(
        "🎯 *Выберите группы для рассылки:*\n\n✅ — выбрана, ⬜ — не выбрана",
        parse_mode="Markdown",
        reply_markup=groups_keyboard(groups)
    )

@dp.callback_query(BroadcastState.selecting_groups)
async def process_group_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = set(data.get("selected", []))
    action = callback.data

    if action == "select_all":
        selected = set(groups.keys())
        await callback.answer("Выбраны все группы")
    elif action == "clear_all":
        selected.clear()
        await callback.answer("Выбор очищен")
    elif action == "send_broadcast":
        if not selected:
            await callback.answer("Выберите хотя бы одну группу!", show_alert=True)
            return
        text = data.get("text")
        await state.update_data(selected=list(selected))
        confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, отправить", callback_data="confirm_send")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")]
        ])
        await callback.message.edit_text(
            f"📢 *Подтверждение рассылки*\n\nТекст:\n{text[:200]}{'...' if len(text) > 200 else ''}\n\n"
            f"👉 В {len(selected)} групп(ы)",
            parse_mode="Markdown",
            reply_markup=confirm_kb
        )
        return
    elif action == "cancel_broadcast":
        await state.clear()
        await callback.message.edit_text("❌ Рассылка отменена", reply_markup=main_menu())
        await callback.answer()
        return
    elif action.startswith("toggle_"):
        chat_id = int(action.split("_")[1])
        if chat_id in selected:
            selected.remove(chat_id)
            await callback.answer("Группа убрана")
        else:
            selected.add(chat_id)
            await callback.answer("Группа добавлена")
    await state.update_data(selected=list(selected))
    await callback.message.edit_reply_markup(reply_markup=groups_keyboard(groups, selected))
    await callback.answer()

@dp.callback_query(F.data == "confirm_send")
async def execute_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data.get("text")
    selected = data.get("selected", [])
    await callback.message.edit_text("🚀 *Отправляю рассылку...*", parse_mode="Markdown")
    success = 0
    fail = 0
    for chat_id in selected:
        try:
            await bot.send_message(chat_id, text, parse_mode="HTML")
            success += 1
            await asyncio.sleep(0.1)
        except Exception:
            fail += 1
    result = f"✅ *Рассылка завершена*\n\n📤 Успешно: {success}\n❌ Ошибок: {fail}"
    await callback.message.edit_text(result, parse_mode="Markdown")
    await state.clear()
    await callback.message.answer("🔙 Вернуться в меню", reply_markup=main_menu())
    await callback.answer()

@dp.callback_query(F.data == "list_groups")
async def list_groups_callback(callback: CallbackQuery):
    if not groups:
        text = "📭 Групп пока нет"
    else:
        text = "📋 *Список групп:*\n\n" + "\n".join(f"• {title}" for title in groups.values())
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())
    await callback.answer()

@dp.callback_query(F.data == "add_here")
async def add_here_callback(callback: CallbackQuery):
    await callback.answer("Используйте команду /add **внутри группы**, которую хотите добавить.", show_alert=True)

@dp.callback_query(F.data == "remove_here")
async def remove_here_callback(callback: CallbackQuery):
    await callback.answer("Используйте команду /remove **внутри группы**, которую хотите удалить.", show_alert=True)

@dp.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено", reply_markup=main_menu())

async def main():
    print("🚀 Бот запущен в режиме polling (Background Worker)")
    print(f"👑 Суперадмины: {SUPER_ADMINS}")
    print(f"👥 Обычные админы: {extra_admins}")
    print(f"📊 Групп в базе: {len(groups)}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())