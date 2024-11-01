import random
import asyncio
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
from nexichat.modules.helpers import chatai, storeai, CHATBOT_ON
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

AUTO_GCASTS = True
CHAT_REFRESH_INTERVAL = 2

chat_cache = []
store_cache = []

lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status

@nexichat.on_message(filters.command("status"))
async def status_command(client: Client, message: Message):
    chat_id = message.chat.id
    chat_status = await status_db.find_one({"chat_id": chat_id})
    if chat_status:
        current_status = chat_status.get("status", "not found")
        await message.reply(f"Chatbot status for this chat: **{current_status}**")
    else:
        await message.reply("No status found for this chat.")

@nexichat.on_message(filters.command("chatbot"))
async def chatbot_command(client: Client, message: Message):
    await message.reply_text(
        f"Chat: {message.chat.title}\n**Choose an option to enable/disable the chatbot.**",
        reply_markup=InlineKeyboardMarkup(CHATBOT_ON),
    )

@nexichat.on_message(filters.incoming)
async def chatbot_response(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        text = message.text
        
        chat_status = await status_db.find_one({"chat_id": chat_id})
        if chat_status and chat_status.get("status") == "disabled":
            return

        if text and any(text.startswith(prefix) for prefix in ["!", "/", ".", "?", "@", "#"]):
            if message.chat.type in ["group", "supergroup"]:
                return await add_served_chat(chat_id)
            else:
                return await add_served_user(chat_id)

        cached_replies = [item for item in store_cache if item["word"] == text]
        
        if cached_replies:
            text_replies = [reply for reply in cached_replies if reply["check"] == "text"]
            non_text_replies = [reply for reply in cached_replies if reply["check"] != "text"]

            if non_text_replies:
                selected_reply = random.choice(non_text_replies)
            elif text_replies:
                selected_reply = text_replies[0]
            else:
                selected_reply = None

            if selected_reply:
                await send_reply_based_on_type(message, selected_reply)
                return

        reply_data = await generate_and_cache_reply(text)
        if reply_data:
            await send_reply_based_on_type(message, reply_data)
        
    except Exception as e:
        print(f"Error handling message: {e}")

async def generate_and_cache_reply(text):
    ai_reply = await generate_ai_reply(text)
    if ai_reply:
        reply_data = {"word": text, "text": ai_reply, "check": "text"}
        store_cache.append(reply_data)
        await save_reply_in_databases(text, reply_data)
        return reply_data
    return None

async def send_reply_based_on_type(message, reply_data):
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

async def save_reply_in_databases(word, reply_data):
    if "_id" in reply_data:
        reply_data.pop("_id")
    reply_data["word"] = word
    try:
        if reply_data["check"] == "text":
            await storeai.insert_one(reply_data)
        else:
            await chatai.insert_one(reply_data)
    except Exception as e:
        print(f"Error saving to database: {e}")

async def generate_ai_reply(text):
    try:
        user_input = f"text: ({text}) Give a short, chatty, fun reply in the same language as the input."
        response = api.chatgpt(user_input)
        return response if response else None
    except Exception as e:
        print(f"Error generating AI reply: {e}")
    return None

async def refresh_replies_cache():
    while True:
        for reply_data in chat_cache:
            if reply_data["check"] == "none" and isinstance(reply_data["text"], str):
                ai_reply = await generate_ai_reply(reply_data["text"])
                if ai_reply:
                    reply_data["text"] = ai_reply
                    print(f"{reply_data["word"]} = {reply_data}")
                    await save_reply_in_databases(reply_data["word"], reply_data)
                    store_cache.append(reply_data)
                chat_cache.remove(reply_data)
        await asyncio.sleep(CHAT_REFRESH_INTERVAL)

async def load_chat_cache():
    global chat_cache
    chat_cache = await chatai.find().to_list(length=None)

async def continuous_update():
    await load_chat_cache()
    while True:
        try:
            await refresh_replies_cache()
        except Exception as e:
            print(f"Error in continuous update: {e}")

if AUTO_GCASTS:
    asyncio.create_task(continuous_update())
