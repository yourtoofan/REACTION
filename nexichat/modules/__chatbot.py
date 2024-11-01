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
                selected_reply = random.choice(reply_data)  # Select random reply from stored replies
                await send_reply_based_on_type(message, selected_reply)
            else:
                # Generate AI-based reply if no stored replies are found
                ai_reply = await generate_ai_reply(message.text)
                if ai_reply:
                    await message.reply_text(ai_reply)
                    await save_reply_in_databases(message.text, {"text": ai_reply, "check": "text"})
                else:
                    await message.reply_text("**I don't understand. What are you saying?**")

    except Exception as e:
        print(f"Error handling message: {e}")

async def send_reply_based_on_type(message, reply_data):
    """Send reply based on type of content in reply_data."""
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

async def get_reply(word: str):
    try:
        # Find multiple responses for the word in `storeai`, else look in `chatai`
        is_chat = await storeai.find({"word": word}).to_list(length=None)
        if not is_chat:
            is_chat = await chatai.find().to_list(length=None)
        return is_chat if is_chat else None
    except Exception as e:
        print(f"Error in get_reply: {e}")
        return None

async def save_reply_in_databases(word, reply_data):
    if "_id" in reply_data:
        reply_data.pop("_id")  # Remove MongoDB's ID if it exists
    reply_data["word"] = word  # Store the word that triggered the reply
    store_cache.append(reply_data)

    try:
        if reply_data["check"] == "text":
            await storeai.insert_one(reply_data)
        else:
            await chatai.insert_one(reply_data)
    except Exception as e:
        print(f"Error saving to database: {e}")

async def generate_ai_reply(text):
    try:
        user_input = f"text: ({text}) Give a short, chatty, fun reply. in same lang in which lang that text is written"
        response = api.chatgpt(user_input)
        if response:
            return response
    except Exception as e:
        print(f"Error generating AI reply: {e}")
    return None

async def refresh_replies_cache():
    while True:
        for reply_data in chat_cache[:]:
            if reply_data["check"] == "text" and isinstance(reply_data["text"], str) and reply_data["text"]:
                ai_reply = await generate_ai_reply(reply_data["text"])
                if ai_reply:
                    reply_data["text"] = ai_reply
                    print("4")
                    await save_reply_in_databases(reply_data["text"], reply_data)
                    chat_cache.remove(reply_data)
                    print(f"New reply saved for {reply_data['text']}")
        await asyncio.sleep(CHAT_REFRESH_INTERVAL)

async def load_chat_cache():
    global chat_cache
    chat_cache = await chatai.find().to_list(length=None)

async def continuous_update():
    await load_chat_cache()
    print("2")
    while True:
        try:
            print("3")
            await refresh_replies_cache()
            print("5")
        except Exception as e:
            print(f"Error in continuous update: {e}")
        
if AUTO_GCASTS:
    print("1")
    asyncio.create_task(continuous_update())
