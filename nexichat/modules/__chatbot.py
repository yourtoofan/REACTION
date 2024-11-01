import random
from TheApi import api
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.errors import MessageEmpty
from pyrogram.enums import ChatAction, ChatMemberStatus as CMS
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from deep_translator import GoogleTranslator
from nexichat.database.chats import add_served_chat
from nexichat.database.users import add_served_user
from config import MONGO_URL
from nexichat import nexichat, mongo, LOGGER, db
from nexichat.modules.helpers import chatai, CHATBOT_ON
from nexichat.modules.helpers import (
    ABOUT_BTN,
    ABOUT_READ,
    ADMIN_READ,
    BACK,
    CHATBOT_BACK,
    CHATBOT_READ,
    DEV_OP,
    HELP_BTN,
    HELP_READ,
    MUSIC_BACK_BTN,
    SOURCE_READ,
    START,
    TOOLS_DATA_READ,
)
import asyncio

translator = GoogleTranslator()

lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status

from langdetect import detect

database_replies_cache = []
ai_generated_replies_cache = []

async def load_replies_cache():
    global database_replies_cache
    database_replies_cache = await chatai.find().to_list(length=None)

async def save_reply(original_message: Message, reply_message: Message):
    global database_replies_cache
    try:
        reply_data = {
            "word": original_message.text,
            "text": None,
            "check": "none",
        }

        if reply_message.sticker:
            reply_data["text"] = reply_message.sticker.file_id
            reply_data["check"] = "sticker"
        elif reply_message.photo:
            reply_data["text"] = reply_message.photo.file_id
            reply_data["check"] = "photo"
        elif reply_message.video:
            reply_data["text"] = reply_message.video.file_id
            reply_data["check"] = "video"
        elif reply_message.audio:
            reply_data["text"] = reply_message.audio.file_id
            reply_data["check"] = "audio"
        elif reply_message.animation:
            reply_data["text"] = reply_message.animation.file_id
            reply_data["check"] = "gif"
        elif reply_message.voice:
            reply_data["text"] = reply_message.voice.file_id
            reply_data["check"] = "voice"
        elif reply_message.text:
            reply_data["text"] = reply_message.text
            reply_data["check"] = "none"

        is_chat = await chatai.find_one(reply_data)
        if not is_chat:
            await chatai.insert_one(reply_data)
            database_replies_cache.append(reply_data)

    except Exception as e:
        print(f"Error in save_reply: {e}")


async def get_reply(word: str):
    relevant_replies = [reply for reply in ai_generated_replies_cache if reply['word'] == word]
    if relevant_replies:
        return random.choice(relevant_replies)

    relevant_replies = [reply for reply in database_replies_cache if reply['word'] == word]
    if relevant_replies:
        return random.choice(relevant_replies)

    return random.choice(database_replies_cache) if database_replies_cache else None

@nexichat.on_message(filters.command("status"))
async def status_command(client: Client, message: Message):
    chat_id = message.chat.id
    chat_status = await status_db.find_one({"chat_id": chat_id})
    if chat_status:
        current_status = chat_status.get("status", "not found")
        await message.reply(f"Chatbot status for this chat: **{current_status}**")
    else:
        await message.reply("No status found for this chat.")


languages = {
    # Top 20 languages used on Telegram
    'english': 'en', 'hindi': 'hi', 'amharic': 'am', 'Myanmar': 'my', 'russian': 'ru',  
    'arabic': 'ar', 'turkish': 'tr', 'german': 'de', 'french': 'fr', 'spanish': 'es',
    'italian': 'it', 'persian': 'fa', 'indonesian': 'id', 'portuguese': 'pt',
    'ukrainian': 'uk', 'filipino': 'tl', 'korean': 'ko', 'japanese': 'ja', 
    'polish': 'pl', 'vietnamese': 'vi', 'thai': 'th', 'dutch': 'nl',

    # Top languages spoken in Bihar
    'bhojpuri': 'bho', 'maithili': 'mai', 'urdu': 'ur', 'tamil': 'ta',
    'bengali': 'bn', 'angika': 'anp', 'sanskrit': 'sa', 'nepali': 'ne',
    'oriya': 'or', 'santhali': 'sat', 'khortha': 'kht', 
    'kurmali': 'kyu', 'ho': 'hoc', 'munda': 'unr', 'kharwar': 'kqw', 
    'mundari': 'unr', 'sadri': 'sck', 'pali': 'pi',

    # Top languages spoken in India
    'telugu': 'te', 'bengali': 'bn', 'marathi': 'mr', 'tamil': 'ta', 
    'gujarati': 'gu', 'urdu': 'ur', 'kannada': 'kn', 'malayalam': 'ml', 
    'odia': 'or', 'punjabi': 'pa', 'assamese': 'as', 'sanskrit': 'sa', 
    'kashmiri': 'ks', 'konkani': 'gom', 'sindhi': 'sd', 'bodo': 'brx', 
    'dogri': 'doi', 'santali': 'sat', 'meitei': 'mni', 'nepali': 'ne',

    # Other language
    'afrikaans': 'af', 'albanian': 'sq', 'armenian': 'hy', 
    'aymara': 'ay', 'azerbaijani': 'az', 'bambara': 'bm', 
    'basque': 'eu', 'belarusian': 'be', 'bosnian': 'bs', 'bulgarian': 'bg', 
    'catalan': 'ca', 'cebuano': 'ceb', 'chichewa': 'ny', 
    'chinese (simplified)': 'zh-CN', 'chinese (traditional)': 'zh-TW', 
    'corsican': 'co', 'croatian': 'hr', 'czech': 'cs', 'danish': 'da', 
    'dhivehi': 'dv', 'esperanto': 'eo', 'estonian': 'et', 'ewe': 'ee', 
    'finnish': 'fi', 'frisian': 'fy', 'galician': 'gl', 'georgian': 'ka', 
    'greek': 'el', 'guarani': 'gn', 'haitian creole': 'ht', 'hausa': 'ha', 
    'hawaiian': 'haw', 'hebrew': 'iw', 'hmong': 'hmn', 'hungarian': 'hu', 
    'icelandic': 'is', 'igbo': 'ig', 'ilocano': 'ilo', 'irish': 'ga', 
    'javanese': 'jw', 'kazakh': 'kk', 'khmer': 'km', 'kinyarwanda': 'rw', 
    'krio': 'kri', 'kurdish (kurmanji)': 'ku', 'kurdish (sorani)': 'ckb', 
    'kyrgyz': 'ky', 'lao': 'lo', 'latin': 'la', 'latvian': 'lv', 
    'lingala': 'ln', 'lithuanian': 'lt', 'luganda': 'lg', 'luxembourgish': 'lb', 
    'macedonian': 'mk', 'malagasy': 'mg', 'maltese': 'mt', 'maori': 'mi', 
    'mizo': 'lus', 'mongolian': 'mn', 'myanmar': 'my', 'norwegian': 'no', 
    'oromo': 'om', 'pashto': 'ps', 'quechua': 'qu', 'romanian': 'ro', 
    'samoan': 'sm', 'scots gaelic': 'gd', 'sepedi': 'nso', 'serbian': 'sr', 
    'sesotho': 'st', 'shona': 'sn', 'sinhala': 'si', 'slovak': 'sk', 
    'slovenian': 'sl', 'somali': 'so', 'sundanese': 'su', 'swahili': 'sw', 
    'swedish': 'sv', 'tajik': 'tg', 'tatar': 'tt', 'tigrinya': 'ti', 
    'tsonga': 'ts', 'turkmen': 'tk', 'twi': 'ak', 'uyghur': 'ug', 
    'uzbek': 'uz', 'welsh': 'cy', 'xhosa': 'xh', 'yiddish': 'yi', 
    'yoruba': 'yo', 'zulu': 'zu'
}



def generate_language_buttons(languages):
    buttons = []
    current_row = []
    for lang, code in languages.items():
        current_row.append(InlineKeyboardButton(lang.capitalize(), callback_data=f'setlang_{code}'))
        if len(current_row) == 4:
            buttons.append(current_row)
            current_row = []
    if current_row:
        buttons.append(current_row)
    return InlineKeyboardMarkup(buttons)

async def get_chat_language(chat_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else "en"
    
@nexichat.on_message(filters.command(["lang", "language", "setlang"]))
async def set_language(client: Client, message: Message):
    await message.reply_text(
        "Please select your chat language:",
        reply_markup=generate_language_buttons(languages)
    )


@nexichat.on_message(filters.command("status"))
async def status_command(client: Client, message: Message):
    chat_id = message.chat.id
    chat_status = await status_db.find_one({"chat_id": chat_id})
    if chat_status:
        current_status = chat_status.get("status", "not found")
        await message.reply(f"Chatbot status for this chat: **{current_status}**")
    else:
        await message.reply("No status found for this chat.")


@nexichat.on_message(filters.command(["lang", "language", "setlang"]))
async def set_language(client: Client, message: Message):
    await message.reply_text(
        "Please select your chat language:",
        reply_markup=generate_language_buttons(languages)
    )


@nexichat.on_message(filters.command(["resetlang", "nolang"]))
async def reset_language(client: Client, message: Message):
    chat_id = message.chat.id
    lang_db.update_one({"chat_id": chat_id}, {"$set": {"language": "nolang"}}, upsert=True)
    await message.reply_text("**Bot language has been reset in this chat to mix language.**")


@nexichat.on_message(filters.command("chatbot"))
async def chatbot_command(client: Client, message: Message):
    await message.reply_text(
        f"Chat: {message.chat.title}\n**Choose an option to enable/disable the chatbot.**",
        reply_markup=InlineKeyboardMarkup(CHATBOT_ON),
    )

import asyncio

AUTO_GCASTS = True
CHAT_REFRESH_INTERVAL = 2

chat_cache = []
store_cache = []

async def load_chat_cache():
    async for reply_data in chatai.find():
        chat_cache.append(reply_data)

async def save_reply_in_databases(reply, reply_data):
    if reply_data["check"] == "text":
        store_cache.append(reply_data)
        await storeai.insert_one(reply_data)
    else:
        store_cache.append(reply_data)
        await chatai.insert_one(reply_data)

async def generate_ai_reply(text):
    try:
        user_input = f"text: ({text}) Give a short, chatty, fun reply."
        response = api.chatgpt(user_input)
        if response:
            return response
    except Exception as e:
        print(f"Error generating AI reply: {e}")
    return None

async def refresh_replies_cache():
    while True:
        for reply_data in list(chat_cache):
            if reply_data["check"] == "text" and isinstance(reply_data["text"], str) and reply_data["text"]:
                ai_reply = await generate_ai_reply(reply_data["text"])
                if ai_reply:
                    reply_data["text"] = ai_reply
                    await save_reply_in_databases(reply_data["text"], reply_data)
                    chat_cache.remove(reply_data)
            await asyncio.sleep(CHAT_REFRESH_INTERVAL)

async def continuous_update():
    await load_chat_cache()
    while True:
        if AUTO_GCASTS:
            try:
                await refresh_replies_cache()
            except Exception as e:
                print(f"Error in continuous update: {e}")
        await asyncio.sleep(1)

async def get_reply(word: str):
    try:
        is_chat = await storeai.find({"word": word}).to_list(length=None)
        if not is_chat:
            is_chat = await chatai.find().to_list(length=None)
        return random.choice(is_chat) if is_chat else None
    except Exception as e:
        print(f"Error in get_reply: {e}")
        return None
        
@nexichat.on_message(filters.incoming)
async def chatbot_response(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        chat_status = await status_db.find_one({"chat_id": chat_id})

        if chat_status and chat_status.get("status") == "disabled":
            return

        if message.text and any(message.text.startswith(prefix) for prefix in ["!", "/", ".", "?", "@", "#"]):
            if message.chat.type in ["group", "supergroup"]:
                return await add_served_chat(chat_id)
            else:
                return await add_served_user(chat_id)
        
        if (message.reply_to_message and message.reply_to_message.from_user.id == nexichat.id) or not message.reply_to_message:
            reply_data = await get_reply(message.text)

            if reply_data:
                
                if reply_data["check"] == "sticker":
                    await message.reply_sticker(reply_data["text"])
                elif reply_data["check"] == "photo":
                    await message.reply_photo(reply_data["text"])
                elif reply_data["check"] == "video":
                    await message.reply_video(reply_data["text"])
                elif reply_data["check"] == "audio":
                    await message.reply_audio(reply_data["text"])
                elif reply_data["check"] == "gif":
                    await message.reply_animation(reply_data["text"])
                elif reply_data["check"] == "voice":
                    await message.reply_voice(reply_data["text"])
                else:
                    await message.reply_text(reply_data["text"])
            else:
                await message.reply_text("**I don't understand. What are you saying?**")

            await save_reply_in_databases(message.reply_to_message, reply_data)

    except Exception as e:
        print(f"Error handling message: {e}")

if AUTO_GCASTS:
    asyncio.create_task(continuous_update())

                    
                        
