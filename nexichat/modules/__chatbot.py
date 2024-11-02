import random
from MukeshAPI import api
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
from nexichat.modules.helpers import chatai, storeai, languages, CHATBOT_ON
from nexichat.modules.helpers import (
    ABOUT_BTN, ABOUT_READ, ADMIN_READ, BACK, CHATBOT_BACK, CHATBOT_READ,
    DEV_OP, HELP_BTN, HELP_READ, MUSIC_BACK_BTN, SOURCE_READ, START,
    TOOLS_DATA_READ,
)
import asyncio
import re

translator = GoogleTranslator()
lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status

replies_cache = []
new_replies_cache = []

async def load_replies_cache():
    global replies_cache
    replies_cache = await chatai.find({"check": "none"}).to_list(length=None)

async def save_reply(original_message: Message, reply_message: Message):
    global replies_cache
    try:
        reply_data = {
            "word": original_message.text,
            "text": None,
            "check": "none",
        }

        if reply_message.sticker:
            reply_data.update({"text": reply_message.sticker.file_id, "check": "sticker"})
        elif reply_message.photo:
            reply_data.update({"text": reply_message.photo.file_id, "check": "photo"})
        elif reply_message.video:
            reply_data.update({"text": reply_message.video.file_id, "check": "video"})
        elif reply_message.audio:
            reply_data.update({"text": reply_message.audio.file_id, "check": "audio"})
        elif reply_message.animation:
            reply_data.update({"text": reply_message.animation.file_id, "check": "gif"})
        elif reply_message.voice:
            reply_data.update({"text": reply_message.voice.file_id, "check": "voice"})
        elif reply_message.text:
            reply_data["text"] = reply_message.text

        is_chat = await chatai.find_one(reply_data)
        if not is_chat:
            await chatai.insert_one(reply_data)
            replies_cache.append(reply_data)

    except Exception as e:
        print(f"Error in save_reply: {e}")

async def get_reply(word: str):
    global replies_cache
    if not replies_cache:
        await load_replies_cache()
        print("Reloaded Chats from database")
    relevant_replies = [reply for reply in replies_cache if reply['word'] == word]
    if not relevant_replies:
        relevant_replies = replies_cache
    return random.choice(relevant_replies) if relevant_replies else None

async def get_new_reply(word: str):
    global new_replies_cache
    if not new_replies_cache:
        await load_replies_cache()
        print("Reloaded Chats from Ai")
    relevant_replies = [reply for reply in new_replies_cache if reply['word'] == word]
    return None

async def get_chat_language(chat_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else "en"

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
            reply_data = await get_new_reply(message.text)
            if reply_data:
                response_text = reply_data["text"]
                chat_lang = await get_chat_language(chat_id)
            else:
                reply_data = await get_reply(message.text)
                response_text = reply_data["text"]
                chat_lang = await get_chat_language(chat_id)
                
                translated_text = response_text if not chat_lang or chat_lang == "nolang" else GoogleTranslator(source='auto', target=chat_lang).translate(response_text)
                
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
                    await message.reply_text(translated_text)
            
        if message.reply_to_message:
            await save_reply(message.reply_to_message, message)

    except MessageEmpty:
        await message.reply_text("🙄🙄")
    except Exception as e:
        return

async def save_new_reply(x, new_reply):
    global new_replies_cache
    try:
        reply_data = {
            "word": x,
            "text": new_reply,
            "check": "none"
        }

        is_chat = await storeai.find_one(reply_data)
        if not is_chat:
            await storeai.insert_one(reply_data)
            await chatai.delete_one(reply_data)
            new_replies_cache.append(reply_data)
            replies_cache.remove(reply_data)
            
    except Exception as e:
        print(f"Error in save_new_reply: {e}")

async def generate_reply(word):
    user_input = f"""
        text:- ({word})
        text me message hai uske liye Ekdam chatty aur chhota reply do jitna chhota se chhota reply me kam ho jaye utna hi chota reply do agar jyada bada reply dena ho to maximum 1 line ka dena barna kosis krna chhota sa chhota reply ho aur purane jaise reply mat dena new reply lagna chahiye aur reply mazedar aur simple ho. Jis language mein yeh text hai, usi language mein reply karo. Agar sirf emoji hai toh bas usi se related emoji bhejo. Dhyaan rahe tum ek ladki ho toh reply bhi ladki ke jaise masti bhara ho.
        Bas reply hi likh ke do, kuch extra nahi aur jitna fast ho sake utna fast reply do!
    """
    response = api.gemini(user_input)
    return response["results"] if response and "results" in response else None

async def creat_reply(word):
    from TheApi import api
    url_pattern = re.compile(r'(https?://\S+)')
    user_input = f"""
        text:- ({word})
        text me message hai uske liye Ekdam chatty aur chhota reply do jitna chhota se chhota reply me kam ho jaye utna hi chota reply do agar jyada bada reply dena ho to maximum 1 line ka dena barna kosis krna chhota sa chhota reply ho aur purane jaise reply mat dena new reply lagna chahiye aur reply mazedar aur simple ho. Jis language mein yeh text hai, usi language mein reply karo. Agar sirf emoji hai toh bas usi se related emoji bhejo. Dhyaan rahe tum ek ladki ho toh reply bhi ladki ke jaise masti bhara ho.
        Bas reply hi likh ke do, kuch extra nahi aur jitna fast ho sake utna fast reply do!
    """
    results = api.chatgpt(user_input)
    if results and url_pattern.search(results):
        return None
    return results

async def update_replies_cache():
    global replies_cache
    url_pattern = re.compile(r'(https?://\S+)')
    
    for reply_data in replies_cache:
        if "text" in reply_data and reply_data["check"] == "none":
            try:
                new_reply = await generate_reply(reply_data["word"])
                x = reply_data["word"]

                if new_reply is None:
                    from TheApi import api
                    new_reply = await creat_reply(reply_data["word"])
                    
                    if new_reply is None:
                        print("API dead")
                        continue

                await save_new_reply(x, new_reply)
                print(f"Saved reply in database for {x} == {new_reply}")
                
            except Exception as e:
                print(f"Error updating reply for {reply_data['word']}: {e}")

        await asyncio.sleep(5)

# Continuous task to load cache and update replies
async def continuous_update():
    await load_replies_cache()
    while True:
        try:
            await update_replies_cache()
        except Exception as e:
            print(f"Error in continuous_update: {e}")
        await asyncio.sleep(5)

# Start the update
asyncio.create_task(continuous_update())
