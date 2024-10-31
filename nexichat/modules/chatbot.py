import random
from TheApi import api
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.errors import MessageEmpty
from pyrogram.enums import ChatAction
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from deep_translator import GoogleTranslator 
from nexichat.database.chats import add_served_chat
from nexichat.database.users import add_served_user
from config import MONGO_URL
from nexichat import nexichat, mongo, db
from pyrogram.types import Message
from nexichat.modules.helpers import CHATBOT_ON
from pymongo import MongoClient
from nexichat import mongo
from pyrogram.enums import ChatMemberStatus as CMS
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup
import asyncio
import config
from nexichat import LOGGER, nexichat
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

translator = GoogleTranslator()
from nexichat import db

# Simplified access to each collection in a consistent way
chatai = db.Word.WordDb
status_db = db.chatbot_status_db.status

@nexichat.on_message(filters.command("status"))
async def status_command(client: Client, message: Message):
    chat_id = message.chat.id

    # Retrieve the status for the given chat_id
    chat_status = await status_db.find_one({"chat_id": chat_id})

    # Check if a status was found
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

@nexichat.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    LOGGER.info(query.data)

    # Help menu
    if query.data == "HELP":
        await query.message.edit_text(
            text=HELP_READ,
            reply_markup=InlineKeyboardMarkup(HELP_BTN),
            disable_web_page_preview=True,
        )

    # Close menu
    elif query.data == "CLOSE":
        await query.message.delete()
        await query.answer("Closed menu!", show_alert=True)

    # Go back to the main menu
    elif query.data == "BACK":
        await query.message.edit(
            text=START,
            reply_markup=InlineKeyboardMarkup(DEV_OP),
        )

    # Show source information
    elif query.data == "SOURCE":
        await query.message.edit(
            text=SOURCE_READ,
            reply_markup=InlineKeyboardMarkup(BACK),
            disable_web_page_preview=True,
        )

    # Show about information
    elif query.data == "ABOUT":
        await query.message.edit(
            text=ABOUT_READ,
            reply_markup=InlineKeyboardMarkup(ABOUT_BTN),
            disable_web_page_preview=True,
        )

    # Show admin information
    elif query.data == "ADMINS":
        await query.message.edit(
            text=ADMIN_READ,
            reply_markup=InlineKeyboardMarkup(MUSIC_BACK_BTN),
        )

    # Show tools information
    elif query.data == "TOOLS_DATA":
        await query.message.edit(
            text=TOOLS_DATA_READ,
            reply_markup=InlineKeyboardMarkup(CHATBOT_BACK),
        )

    # Back to the help menu
    elif query.data == "BACK_HELP":
        await query.message.edit(
            text=HELP_READ,
            reply_markup=InlineKeyboardMarkup(HELP_BTN),
        )

    # Chatbot commands
    elif query.data == "CHATBOT_CMD":
        await query.message.edit(
            text=CHATBOT_READ,
            reply_markup=InlineKeyboardMarkup(CHATBOT_BACK),
        )

    # Back to the chatbot menu
    elif query.data == "CHATBOT_BACK":
        await query.message.edit(
            text=HELP_READ,
            reply_markup=InlineKeyboardMarkup(HELP_BTN),
        )

    # Enable chatbot for the chat
    elif query.data == "enable_chatbot":
        chat_id = query.message.chat.id
        status_db.update_one({"chat_id": chat_id}, {"$set": {"status": "enabled"}}, upsert=True)
        await query.answer("Chatbot enabled ✅", show_alert=True)
        await query.edit_message_text(
            f"Chat: {query.message.chat.title}\n**Chatbot has been enabled.**"
        )

    # Disable chatbot for the chat
    elif query.data == "disable_chatbot":
        chat_id = query.message.chat.id
        status_db.update_one({"chat_id": chat_id}, {"$set": {"status": "disabled"}}, upsert=True)
        await query.answer("Chatbot disabled!", show_alert=True)
        await query.edit_message_text(
            f"Chat: {query.message.chat.title}\n**Chatbot has been disabled.**"
        )

   

        
@nexichat.on_message(filters.incoming)
async def chatbot_response(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        chat_status = await status_db.find_one({"chat_id": chat_id})
        
        if chat_status and chat_status.get("status") == "disabled":
            return

        if message.text and any(message.text.startswith(prefix) for prefix in ["!", "/", ".", "?", "@", "#"]):
            if message.chat.type == "group" or message.chat.type == "supergroup":
                return await add_served_chat(message.chat.id)
            else:
                return await add_served_user(message.chat.id)
        
        if (message.reply_to_message and message.reply_to_message.from_user.id == nexichat.id) or not message.reply_to_message:
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)
            reply_data = await get_reply(message.text)

            if reply_data:
                #response_text = reply_data["text"]
                user_input = f"""
                Sentences :- {message.text}
                Ye sentences ka chatbot jaisa chhota se chhota reply do jyada bada reply mat dena maximum 1 sentence ka hona chahiye reply aur agar chhota se chhota reply me bhi kam ho ja rha hai to chhota hi reply do aur jis lang me sentence hai usi lang me likh ke do, agar sentence me sirf emoji hoga to tum bhi reply me bas emoji do related emoji hi bhejna aur han ladki jaisa reply krna mtlb tum ek ladki ho ok.
               
                Bas reply likh ke do uske alava kuch nhi
                """
                results = api.chatgpt(user_input) 
                
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
                else:
                    await message.reply_text(results)
            else:
                await message.reply_text("**I don't understand. what are you saying??**")
        
        if message.reply_to_message:
            await save_reply(message.reply_to_message, message)
    except MessageEmpty as e:
        return await message.reply_text("🙄🙄")
    except Exception as e:
        return

async def save_reply(original_message: Message, reply_message: Message):
    try:
        if reply_message.sticker:
            is_chat = await chatai.find_one({
                "word": original_message.text,
                "text": reply_message.sticker.file_id,
                "check": "sticker",
            })
            if not is_chat:
                await chatai.insert_one({
                    "word": original_message.text,
                    "text": reply_message.sticker.file_id,
                    "check": "sticker",
                })

        elif reply_message.photo:
            is_chat = await chatai.find_one({
                "word": original_message.text,
                "text": reply_message.photo.file_id,
                "check": "photo",
            })
            if not is_chat:
                await chatai.insert_one({
                    "word": original_message.text,
                    "text": reply_message.photo.file_id,
                    "check": "photo",
                })

        elif reply_message.video:
            is_chat = await chatai.find_one({
                "word": original_message.text,
                "text": reply_message.video.file_id,
                "check": "video",
            })
            if not is_chat:
                await chatai.insert_one({
                    "word": original_message.text,
                    "text": reply_message.video.file_id,
                    "check": "video",
                })

        elif reply_message.audio:
            is_chat = await chatai.find_one({
                "word": original_message.text,
                "text": reply_message.audio.file_id,
                "check": "audio",
            })
            if not is_chat:
                await chatai.insert_one({
                    "word": original_message.text,
                    "text": reply_message.audio.file_id,
                    "check": "audio",
                })

        elif reply_message.animation:  
            is_chat = await chatai.find_one({
                "word": original_message.text,
                "text": reply_message.animation.file_id,
                "check": "gif",
            })
            if not is_chat:
                await chatai.insert_one({
                    "word": original_message.text,
                    "text": reply_message.animation.file_id,
                    "check": "gif",
                })

        elif reply_message.text:
            is_chat = await chatai.find_one({
                "word": original_message.text,
                "text": reply_message.text,
                "check": "none",
            })
            if not is_chat:
                await chatai.insert_one({
                    "word": original_message.text,
                    "text": reply_message.text,
                    "check": "none",
                })

    except Exception as e:
        print(f"Error in save_reply: {e}")

async def get_reply(word: str):
    try:
        is_chat = await chatai.find({"word": word}).to_list(length=None)
        if not is_chat:
            is_chat = await chatai.find().to_list(length=None)
        return random.choice(is_chat) if is_chat else None
    except Exception as e:
        print(f"Error in get_reply: {e}")
        return None
