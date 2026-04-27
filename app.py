{\rtf1\ansi\ansicpg1251\cocoartf2868
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import asyncio\
import json\
import os\
from aiogram import Bot, Dispatcher, types, F\
from aiogram.filters import Command\
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery\
from aiogram.fsm.state import State, StatesGroup\
from aiogram.fsm.context import FSMContext\
from aiogram.fsm.storage.memory import MemoryStorage\
from flask import Flask, request\
import threading\
\
# ===== \uc0\u1058 \u1042 \u1054 \u1048  \u1044 \u1040 \u1053 \u1053 \u1067 \u1045  =====\
BOT_TOKEN = "8768778011:AAGy_xl12xKhrGdZ6iVK28TS5w-OANuAlRM"\
ADMIN_IDS = [284954186]\
# =======================\
\
# Flask \uc0\u1087 \u1088 \u1080 \u1083 \u1086 \u1078 \u1077 \u1085 \u1080 \u1077  \u1076 \u1083 \u1103  healthcheck\
app_flask = Flask(__name__)\
\
@app_flask.route('/')\
@app_flask.route('/health')\
def health():\
    return "Bot is running", 200\
\
# Telegram \uc0\u1073 \u1086 \u1090 \
bot = Bot(token=BOT_TOKEN)\
storage = MemoryStorage()\
dp = Dispatcher(storage=storage)\
\
GROUPS_FILE = "groups.json"\
\
def load_groups():\
    if os.path.exists(GROUPS_FILE):\
        with open(GROUPS_FILE, 'r', encoding='utf-8') as f:\
            data = json.load(f)\
            return \{int(k): v for k, v in data.items()\}\
    return \{\}\
\
def save_groups(groups):\
    with open(GROUPS_FILE, 'w', encoding='utf-8') as f:\
        json.dump(groups, f, ensure_ascii=False, indent=2)\
\
groups = load_groups()\
\
class BroadcastState(StatesGroup):\
    waiting_for_text = State()\
    selecting_groups = State()\
\
def main_menu():\
    keyboard = InlineKeyboardMarkup(inline_keyboard=[\
        [InlineKeyboardButton(text="\uc0\u55357 \u56546  \u1057 \u1076 \u1077 \u1083 \u1072 \u1090 \u1100  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1091 ", callback_data="broadcast")],\
        [InlineKeyboardButton(text="\uc0\u55357 \u56523  \u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1075 \u1088 \u1091 \u1087 \u1087 ", callback_data="list")],\
        [InlineKeyboardButton(text="\uc0\u10133  \u1044 \u1086 \u1073 \u1072 \u1074 \u1080 \u1090 \u1100  \u1101 \u1090 \u1091  \u1075 \u1088 \u1091 \u1087 \u1087 \u1091 ", callback_data="add_here")],\
        [InlineKeyboardButton(text="\uc0\u10134  \u1059 \u1076 \u1072 \u1083 \u1080 \u1090 \u1100  \u1101 \u1090 \u1091  \u1075 \u1088 \u1091 \u1087 \u1087 \u1091 ", callback_data="remove_here")]\
    ])\
    return keyboard\
\
def groups_keyboard(groups_dict, selected=None):\
    if selected is None:\
        selected = set()\
    \
    buttons = []\
    for chat_id, title in groups_dict.items():\
        short_title = title[:25] + "..." if len(title) > 25 else title\
        check = "\uc0\u9989  " if chat_id in selected else "\u11036  "\
        buttons.append([InlineKeyboardButton(\
            text=f"\{check\}\{short_title\}",\
            callback_data=f"toggle_\{chat_id\}"\
        )])\
    \
    buttons.append([\
        InlineKeyboardButton(text="\uc0\u9989  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1074 \u1089 \u1077 ", callback_data="select_all"),\
        InlineKeyboardButton(text="\uc0\u10060  \u1054 \u1095 \u1080 \u1089 \u1090 \u1080 \u1090 \u1100  \u1074 \u1089 \u1077 ", callback_data="clear_all")\
    ])\
    buttons.append([\
        InlineKeyboardButton(text="\uc0\u55357 \u56548  \u1054 \u1090 \u1087 \u1088 \u1072 \u1074 \u1080 \u1090 \u1100 ", callback_data="send"),\
        InlineKeyboardButton(text="\uc0\u10060  \u1054 \u1090 \u1084 \u1077 \u1085 \u1072 ", callback_data="cancel")\
    ])\
    \
    return InlineKeyboardMarkup(inline_keyboard=buttons)\
\
def is_admin(user_id):\
    return user_id in ADMIN_IDS\
\
@dp.message(Command("start"))\
async def start(message: Message):\
    if not is_admin(message.from_user.id):\
        await message.answer("\uc0\u9940  \u1053 \u1077 \u1090  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1072 ")\
        return\
    \
    await message.answer(\
        "\uc0\u55358 \u56605  *\u1055 \u1086 \u1084 \u1086 \u1097 \u1085 \u1080 \u1082  \u1082 \u1086 \u1086 \u1088 \u1076 \u1080 \u1085 \u1072 \u1090 \u1086 \u1088 \u1072 *\\n\\n"\
        "\uc0\u55357 \u56524  *\u1050 \u1072 \u1082  \u1076 \u1086 \u1073 \u1072 \u1074 \u1080 \u1090 \u1100  \u1075 \u1088 \u1091 \u1087 \u1087 \u1091 :*\\n"\
        "1. \uc0\u1044 \u1086 \u1073 \u1072 \u1074 \u1100  \u1073 \u1086 \u1090 \u1072  \u1074  \u1075 \u1088 \u1091 \u1087 \u1087 \u1091  \u1080  \u1076 \u1072 \u1081  \u1087 \u1088 \u1072 \u1074 \u1072  \u1072 \u1076 \u1084 \u1080 \u1085 \u1072 \\n"\
        "2. \uc0\u1042  \u1075 \u1088 \u1091 \u1087 \u1087 \u1077  \u1085 \u1072 \u1087 \u1080 \u1096 \u1080  /start \u1080  \u1085 \u1072 \u1078 \u1084 \u1080  \'ab\u1044 \u1086 \u1073 \u1072 \u1074 \u1080 \u1090 \u1100  \u1101 \u1090 \u1091  \u1075 \u1088 \u1091 \u1087 \u1087 \u1091 \'bb\\n\\n"\
        "\uc0\u55357 \u56546  \u1044 \u1083 \u1103  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1080  \u1085 \u1072 \u1078 \u1084 \u1080  \'ab\u1057 \u1076 \u1077 \u1083 \u1072 \u1090 \u1100  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1091 \'bb\\n\\n"\
        "\uc0\u9889  *\u1050 \u1086 \u1084 \u1072 \u1085 \u1076 \u1099 :*\\n"\
        "/add - \uc0\u1076 \u1086 \u1073 \u1072 \u1074 \u1080 \u1090 \u1100  \u1090 \u1077 \u1082 \u1091 \u1097 \u1091 \u1102  \u1075 \u1088 \u1091 \u1087 \u1087 \u1091 \\n"\
        "/remove - \uc0\u1091 \u1076 \u1072 \u1083 \u1080 \u1090 \u1100  \u1090 \u1077 \u1082 \u1091 \u1097 \u1091 \u1102  \u1075 \u1088 \u1091 \u1087 \u1087 \u1091 \\n"\
        "/groups - \uc0\u1089 \u1087 \u1080 \u1089 \u1086 \u1082  \u1075 \u1088 \u1091 \u1087 \u1087 \\n"\
        "/cancel - \uc0\u1086 \u1090 \u1084 \u1077 \u1085 \u1080 \u1090 \u1100  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1091 ",\
        parse_mode="Markdown",\
        reply_markup=main_menu()\
    )\
\
@dp.message(Command("add"))\
async def add_group(message: Message):\
    if not is_admin(message.from_user.id):\
        return\
    \
    if message.chat.type not in ["group", "supergroup"]:\
        await message.answer("\uc0\u10060  \u1069 \u1090 \u1072  \u1082 \u1086 \u1084 \u1072 \u1085 \u1076 \u1072  \u1088 \u1072 \u1073 \u1086 \u1090 \u1072 \u1077 \u1090  \u1090 \u1086 \u1083 \u1100 \u1082 \u1086  \u1074  \u1075 \u1088 \u1091 \u1087 \u1087 \u1072 \u1093 ")\
        return\
    \
    chat_id = message.chat.id\
    title = message.chat.title\
    \
    try:\
        member = await bot.get_chat_member(chat_id, bot.id)\
        if member.status not in ["administrator", "creator"]:\
            await message.answer("\uc0\u10060  \u1041 \u1086 \u1090  \u1085 \u1077  \u1103 \u1074 \u1083 \u1103 \u1077 \u1090 \u1089 \u1103  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1086 \u1084 ! \u1044 \u1086 \u1073 \u1072 \u1074 \u1100  \u1073 \u1086 \u1090 \u1072  \u1074  \u1072 \u1076 \u1084 \u1080 \u1085 \u1099 .")\
            return\
    except:\
        await message.answer("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1072 . \u1059 \u1073 \u1077 \u1076 \u1080 \u1089 \u1100 , \u1095 \u1090 \u1086  \u1073 \u1086 \u1090  \u1076 \u1086 \u1073 \u1072 \u1074 \u1083 \u1077 \u1085  \u1074  \u1075 \u1088 \u1091 \u1087 \u1087 \u1091 .")\
        return\
    \
    groups[chat_id] = title\
    save_groups(groups)\
    await message.answer(f"\uc0\u9989  \u1043 \u1088 \u1091 \u1087 \u1087 \u1072  \'ab\{title\}\'bb \u1076 \u1086 \u1073 \u1072 \u1074 \u1083 \u1077 \u1085 \u1072  \u1074  \u1089 \u1087 \u1080 \u1089 \u1086 \u1082  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1080 !")\
\
@dp.message(Command("remove"))\
async def remove_group(message: Message):\
    if not is_admin(message.from_user.id):\
        return\
    \
    if message.chat.type not in ["group", "supergroup"]:\
        await message.answer("\uc0\u10060  \u1069 \u1090 \u1072  \u1082 \u1086 \u1084 \u1072 \u1085 \u1076 \u1072  \u1088 \u1072 \u1073 \u1086 \u1090 \u1072 \u1077 \u1090  \u1090 \u1086 \u1083 \u1100 \u1082 \u1086  \u1074  \u1075 \u1088 \u1091 \u1087 \u1087 \u1072 \u1093 ")\
        return\
    \
    chat_id = message.chat.id\
    if chat_id in groups:\
        title = groups[chat_id]\
        del groups[chat_id]\
        save_groups(groups)\
        await message.answer(f"\uc0\u9989  \u1043 \u1088 \u1091 \u1087 \u1087 \u1072  \'ab\{title\}\'bb \u1091 \u1076 \u1072 \u1083 \u1077 \u1085 \u1072  \u1080 \u1079  \u1089 \u1087 \u1080 \u1089 \u1082 \u1072 ")\
    else:\
        await message.answer("\uc0\u10060  \u1069 \u1090 \u1072  \u1075 \u1088 \u1091 \u1087 \u1087 \u1072  \u1085 \u1077  \u1074  \u1089 \u1087 \u1080 \u1089 \u1082 \u1077  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1080 ")\
\
@dp.message(Command("groups"))\
async def show_groups(message: Message):\
    if not is_admin(message.from_user.id):\
        return\
    \
    if not groups:\
        await message.answer("\uc0\u55357 \u56557  \u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1075 \u1088 \u1091 \u1087 \u1087  \u1087 \u1091 \u1089 \u1090 . \u1044 \u1086 \u1073 \u1072 \u1074 \u1100  \u1075 \u1088 \u1091 \u1087 \u1087 \u1099  \u1095 \u1077 \u1088 \u1077 \u1079  /add")\
    else:\
        text = "\uc0\u55357 \u56523  *\u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1075 \u1088 \u1091 \u1087 \u1087 :*\\n\\n"\
        for title in groups.values():\
            text += f"\'95 \{title\}\\n"\
        await message.answer(text, parse_mode="Markdown")\
\
@dp.callback_query(F.data == "broadcast")\
async def start_broadcast(callback: CallbackQuery, state: FSMContext):\
    if not is_admin(callback.from_user.id):\
        await callback.answer("\uc0\u1053 \u1077 \u1090  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1072 ")\
        return\
    \
    if not groups:\
        await callback.message.edit_text("\uc0\u55357 \u56557  \u1053 \u1077 \u1090  \u1075 \u1088 \u1091 \u1087 \u1087 ! \u1044 \u1086 \u1073 \u1072 \u1074 \u1100  \u1075 \u1088 \u1091 \u1087 \u1087 \u1099  \u1095 \u1077 \u1088 \u1077 \u1079  /add", reply_markup=main_menu())\
        await callback.answer()\
        return\
    \
    await state.set_state(BroadcastState.waiting_for_text)\
    await callback.message.edit_text(\
        "\uc0\u9997 \u65039  *\u1053 \u1072 \u1087 \u1080 \u1096 \u1080  \u1090 \u1077 \u1082 \u1089 \u1090  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1080 *\\n\\n"\
        "\uc0\u1058 \u1077 \u1082 \u1089 \u1090  \u1084 \u1086 \u1078 \u1085 \u1086  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1080 \u1088 \u1086 \u1074 \u1072 \u1090 \u1100 :\\n"\
        "\'95 <b>\uc0\u1078 \u1080 \u1088 \u1085 \u1099 \u1081 </b>\\n"\
        "\'95 <i>\uc0\u1082 \u1091 \u1088 \u1089 \u1080 \u1074 </i>\\n"\
        "\'95 <u>\uc0\u1087 \u1086 \u1076 \u1095 \u1077 \u1088 \u1082 \u1085 \u1091 \u1090 \u1099 \u1081 </u>\\n\\n"\
        "\uc0\u1054 \u1090 \u1087 \u1088 \u1072 \u1074 \u1100  /cancel \u1076 \u1083 \u1103  \u1086 \u1090 \u1084 \u1077 \u1085 \u1099 ",\
        parse_mode="Markdown"\
    )\
    await callback.answer()\
\
@dp.message(BroadcastState.waiting_for_text)\
async def get_broadcast_text(message: Message, state: FSMContext):\
    if not is_admin(message.from_user.id):\
        return\
    \
    await state.update_data(text=message.text)\
    await state.set_state(BroadcastState.selecting_groups)\
    \
    await message.answer(\
        "\uc0\u55356 \u57263  *\u1042 \u1099 \u1073 \u1077 \u1088 \u1080  \u1075 \u1088 \u1091 \u1087 \u1087 \u1099  \u1076 \u1083 \u1103  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1080 :*\\n\\n"\
        "\uc0\u9989  - \u1075 \u1088 \u1091 \u1087 \u1087 \u1072  \u1074 \u1099 \u1073 \u1088 \u1072 \u1085 \u1072 \\n"\
        "\uc0\u11036  - \u1075 \u1088 \u1091 \u1087 \u1087 \u1072  \u1085 \u1077  \u1074 \u1099 \u1073 \u1088 \u1072 \u1085 \u1072 ",\
        parse_mode="Markdown",\
        reply_markup=groups_keyboard(groups)\
    )\
\
@dp.callback_query(BroadcastState.selecting_groups)\
async def select_groups(callback: CallbackQuery, state: FSMContext):\
    data = await state.get_data()\
    selected = set(data.get("selected", []))\
    \
    if callback.data == "select_all":\
        selected = set(groups.keys())\
        await callback.answer("\uc0\u9989  \u1042 \u1099 \u1073 \u1088 \u1072 \u1085 \u1099  \u1074 \u1089 \u1077  \u1075 \u1088 \u1091 \u1087 \u1087 \u1099 ")\
    \
    elif callback.data == "clear_all":\
        selected.clear()\
        await callback.answer("\uc0\u10060  \u1042 \u1089 \u1077  \u1075 \u1088 \u1091 \u1087 \u1087 \u1099  \u1086 \u1095 \u1080 \u1097 \u1077 \u1085 \u1099 ")\
    \
    elif callback.data == "send":\
        if not selected:\
            await callback.answer("\uc0\u10060  \u1042 \u1099 \u1073 \u1077 \u1088 \u1080  \u1093 \u1086 \u1090 \u1103  \u1073 \u1099  \u1086 \u1076 \u1085 \u1091  \u1075 \u1088 \u1091 \u1087 \u1087 \u1091 !", show_alert=True)\
            return\
        \
        text = data.get("text")\
        await state.update_data(selected=list(selected))\
        \
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[\
            [InlineKeyboardButton(text="\uc0\u9989  \u1044 \u1072 , \u1086 \u1090 \u1087 \u1088 \u1072 \u1074 \u1080 \u1090 \u1100 ", callback_data="confirm")],\
            [InlineKeyboardButton(text="\uc0\u10060  \u1054 \u1090 \u1084 \u1077 \u1085 \u1072 ", callback_data="cancel")]\
        ])\
        \
        await callback.message.edit_text(\
            f"\uc0\u55357 \u56546  *\u1055 \u1086 \u1076 \u1090 \u1074 \u1077 \u1088 \u1078 \u1076 \u1077 \u1085 \u1080 \u1077  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1080 *\\n\\n"\
            f"\uc0\u1058 \u1077 \u1082 \u1089 \u1090 :\\n\{text[:200]\}\{'...' if len(text) > 200 else ''\}\\n\\n"\
            f"\uc0\u55357 \u56522  \u1055 \u1086 \u1083 \u1091 \u1095 \u1072 \u1090 \u1077 \u1083 \u1077 \u1081 : \{len(selected)\} \u1075 \u1088 \u1091 \u1087 \u1087 \\n\\n"\
            f"\uc0\u1054 \u1090 \u1087 \u1088 \u1072 \u1074 \u1080 \u1090 \u1100 ?",\
            parse_mode="Markdown",\
            reply_markup=confirm_keyboard\
        )\
        return\
    \
    elif callback.data == "cancel":\
        await state.clear()\
        await callback.message.edit_text("\uc0\u10060  \u1056 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1072  \u1086 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1072 ", reply_markup=main_menu())\
        await callback.answer()\
        return\
    \
    elif callback.data.startswith("toggle_"):\
        chat_id = int(callback.data.split("_")[1])\
        if chat_id in selected:\
            selected.remove(chat_id)\
            await callback.answer("\uc0\u10060  \u1043 \u1088 \u1091 \u1087 \u1087 \u1072  \u1091 \u1073 \u1088 \u1072 \u1085 \u1072 ")\
        else:\
            selected.add(chat_id)\
            await callback.answer("\uc0\u9989  \u1043 \u1088 \u1091 \u1087 \u1087 \u1072  \u1076 \u1086 \u1073 \u1072 \u1074 \u1083 \u1077 \u1085 \u1072 ")\
    \
    await state.update_data(selected=list(selected))\
    await callback.message.edit_reply_markup(\
        reply_markup=groups_keyboard(groups, selected)\
    )\
\
@dp.callback_query(F.data == "confirm")\
async def send_broadcast(callback: CallbackQuery, state: FSMContext):\
    data = await state.get_data()\
    text = data.get("text")\
    selected = data.get("selected", [])\
    \
    await callback.message.edit_text("\uc0\u55357 \u56960  *\u1054 \u1090 \u1087 \u1088 \u1072 \u1074 \u1083 \u1103 \u1102  \u1088 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1091 ...*", parse_mode="Markdown")\
    \
    success = 0\
    fail = 0\
    fail_titles = []\
    \
    for chat_id in selected:\
        try:\
            await bot.send_message(chat_id, text, parse_mode="HTML")\
            success += 1\
            await asyncio.sleep(0.1)\
        except Exception as e:\
            fail += 1\
            fail_titles.append(groups.get(chat_id, str(chat_id)))\
    \
    result_text = f"\uc0\u9989  *\u1056 \u1072 \u1089 \u1089 \u1099 \u1083 \u1082 \u1072  \u1079 \u1072 \u1074 \u1077 \u1088 \u1096 \u1077 \u1085 \u1072 !*\\n\\n\u55357 \u56548  \u1059 \u1089 \u1087 \u1077 \u1096 \u1085 \u1086 : \{success\}\\n\u10060  \u1054 \u1096 \u1080 \u1073 \u1086 \u1082 : \{fail\}"\
    \
    if fail_titles:\
        result_text += f"\\n\\n\uc0\u9888 \u65039  \u1054 \u1096 \u1080 \u1073 \u1082 \u1080  \u1074  \u1075 \u1088 \u1091 \u1087 \u1087 \u1072 \u1093 :\\n" + "\\n".join(f"\'95 \{t\}" for t in fail_titles[:5])\
    \
    await callback.message.edit_text(result_text, parse_mode="Markdown")\
    await callback.message.answer("\uc0\u55357 \u56601  \u1042 \u1077 \u1088 \u1085 \u1091 \u1090 \u1100 \u1089 \u1103  \u1074  \u1084 \u1077 \u1085 \u1102 ", reply_markup=main_menu())\
    await state.clear()\
    await callback.answer()\
\
@dp.callback_query(F.data == "list")\
async def list_groups(callback: CallbackQuery):\
    if not groups:\
        text = "\uc0\u55357 \u56557  \u1043 \u1088 \u1091 \u1087 \u1087  \u1087 \u1086 \u1082 \u1072  \u1085 \u1077 \u1090 "\
    else:\
        text = "\uc0\u55357 \u56523  *\u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1075 \u1088 \u1091 \u1087 \u1087 :*\\n\\n" + "\\n".join(f"\'95 \{title\}" for title in groups.values())\
    \
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())\
    await callback.answer()\
\
@dp.callback_query(F.data == "add_here")\
async def add_here(callback: CallbackQuery):\
    await callback.answer("\uc0\u1053 \u1072 \u1087 \u1080 \u1096 \u1080  /add \u1074  \u1075 \u1088 \u1091 \u1087 \u1087 \u1077 , \u1075 \u1076 \u1077  \u1093 \u1086 \u1095 \u1077 \u1096 \u1100  \u1076 \u1086 \u1073 \u1072 \u1074 \u1080 \u1090 \u1100  \u1073 \u1086 \u1090 \u1072 ", show_alert=True)\
\
@dp.callback_query(F.data == "remove_here")\
async def remove_here(callback: CallbackQuery):\
    await callback.answer("\uc0\u1053 \u1072 \u1087 \u1080 \u1096 \u1080  /remove \u1074  \u1075 \u1088 \u1091 \u1087 \u1087 \u1077 , \u1082 \u1086 \u1090 \u1086 \u1088 \u1091 \u1102  \u1093 \u1086 \u1095 \u1077 \u1096 \u1100  \u1091 \u1076 \u1072 \u1083 \u1080 \u1090 \u1100 ", show_alert=True)\
\
@dp.message(Command("cancel"))\
async def cancel(message: Message, state: FSMContext):\
    await state.clear()\
    await message.answer("\uc0\u10060  \u1044 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077  \u1086 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086 ", reply_markup=main_menu())\
\
async def main():\
    print("=" * 40)\
    print("\uc0\u55358 \u56605  \u1055 \u1086 \u1084 \u1086 \u1097 \u1085 \u1080 \u1082  \u1082 \u1086 \u1086 \u1088 \u1076 \u1080 \u1085 \u1072 \u1090 \u1086 \u1088 \u1072 ")\
    print("=" * 40)\
    print(f"\uc0\u9989  \u1041 \u1086 \u1090  \u1079 \u1072 \u1087 \u1091 \u1097 \u1077 \u1085 ")\
    print(f"\uc0\u55357 \u56522  \u1043 \u1088 \u1091 \u1087 \u1087  \u1074  \u1073 \u1072 \u1079 \u1077 : \{len(groups)\}")\
    print("=" * 40)\
    \
    # \uc0\u1047 \u1072 \u1087 \u1091 \u1089 \u1082 \u1072 \u1077 \u1084  Flask \u1074  \u1086 \u1090 \u1076 \u1077 \u1083 \u1100 \u1085 \u1086 \u1084  \u1087 \u1086 \u1090 \u1086 \u1082 \u1077  \u1076 \u1083 \u1103  healthcheck\
    def run_flask():\
        port = int(os.environ.get("PORT", 8080))\
        app_flask.run(host="0.0.0.0", port=port)\
    \
    flask_thread = threading.Thread(target=run_flask)\
    flask_thread.start()\
    \
    # \uc0\u1047 \u1072 \u1087 \u1091 \u1089 \u1082 \u1072 \u1077 \u1084  \u1073 \u1086 \u1090 \u1072 \
    await dp.start_polling(bot)\
\
if __name__ == "__main__":\
    asyncio.run(main())}