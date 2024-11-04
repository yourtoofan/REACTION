import random
import asyncio
import re
from MukeshAPI import api
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.errors import MessageEmpty
from pyrogram.enums import ChatAction, ChatMemberStatus as CMS
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from deep_translator import GoogleTranslator
from nexichat.database.chats import add_served_chat
from nexichat.database.users import add_served_user
from datetime import datetime, timedelta
from nexichat import nexichat, mongo, LOGGER, db
from nexichat.modules.helpers import chatai, storeai, languages, CHATBOT_ON
from nexichat.modules.helpers import (
    ABOUT_BTN, ABOUT_READ, ADMIN_READ, BACK, CHATBOT_BACK, CHATBOT_READ,
    DEV_OP, HELP_BTN, HELP_READ, MUSIC_BACK_BTN, SOURCE_READ, START,
    TOOLS_DATA_READ,
)

translator = GoogleTranslator()
lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status
replies_cache = []
new_replies_cache = []

blocklist = {}
message_counts = {}


async def get_reply(message):
    global replies_cache, new_replies_cache
    try:
        if message.text:
            message_id = message.text
            message_type = "text"
        elif message.sticker:
            message_id = message.sticker.file_id
            message_type = "sticker"
        elif message.photo:
            message_id = message.photo.file_id
            message_type = "photo"
        elif message.video:
            message_id = message.video.file_id
            message_type = "video"
        elif message.audio:
            message_id = message.audio.file_id
            message_type = "audio"
        elif message.animation:
            message_id = message.animation.file_id
            message_type = "gif"
        elif message.voice:
            message_id = message.voice.file_id
            message_type = "voice"
        else:
            return None, None

        for reply_data in new_replies_cache:
            if reply_data["word"] == message_id and reply_data["check"] == message_type:
                return reply_data["text"], reply_data["check"]
        
        reply_data = await storeai.find_one({"word": message_id, "check": message_type})
        if reply_data:
            new_replies_cache.append(reply_data)
            return reply_data["text"], reply_data["check"]

        if new_replies_cache:
            random_reply = random.choice(new_replies_cache)
            return random_reply["text"], random_reply["check"]
        
        await load_replies_cache()
        return None, None

    except Exception as e:
        print(f"Error in get_reply: {e}")
        return None, None

async def get_chat_language(chat_id):
    try:
        chat_lang = await lang_db.find_one({"chat_id": chat_id})
        return chat_lang["language"] if chat_lang and "language" in chat_lang else "en"
    except Exception as e:
        print(f"Error in get_chat_language: {e}")
        return "en"

@nexichat.on_message(filters.incoming)
async def chatbot_response(client: Client, message: Message):
    global blocklist, message_counts
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        current_time = datetime.now()
        
        blocklist = {uid: time for uid, time in blocklist.items() if time > current_time}

        if user_id in blocklist:
            return

        if user_id not in message_counts:
            message_counts[user_id] = {"count": 1, "last_time": current_time}
        else:
            time_diff = (current_time - message_counts[user_id]["last_time"]).total_seconds()
            if time_diff <= 3:
                message_counts[user_id]["count"] += 1
            else:
                message_counts[user_id] = {"count": 1, "last_time": current_time}
            
            if message_counts[user_id]["count"] >= 4:
                blocklist[user_id] = current_time + timedelta(minutes=1)
                message_counts.pop(user_id, None)
                await message.reply_text(f"**Hey, {message.from_user.mention}**\n\n**You are blocked for 1 minute due to spam messages.**\n**Try again after 1 minute 🤣.**")
                return
                
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
            reply_data = await get_reply(message)
            if reply_data:
                response_text, reply_type = reply_data
        
                try:
                    if reply_type == "sticker":
                        await message.reply_sticker(response_text)
                    elif reply_type == "photo":
                        await message.reply_photo(response_text)
                    elif reply_type == "video":
                        await message.reply_video(response_text)
                    elif reply_type == "audio":
                        await message.reply_audio(response_text)
                    elif reply_type == "gif":
                        await message.reply_animation(response_text)
                    elif reply_type == "voice":
                        await message.reply_voice(response_text)
                    elif reply_type == "text":
                        chat_lang = await get_chat_language(chat_id)
                        if chat_lang and chat_lang != "nolang":
                            translated_text = GoogleTranslator(source='auto', target=chat_lang).translate(response_text)
                        else:
                            translated_text = response_text
                        await message.reply_text(translated_text)

                except Exception as e:
                    print(f"Error while replying: {e}")
                    
        
        if message.reply_to_message:
            await save_reply(message.reply_to_message, message)
            
        if message.text:
            await save_text(message)


    except Exception as vip:
        return await message.reply_text("🙄🙄")
        
async def save_text(original_message: Message):
    global replies_cache
    try:
        if original_message.text:
            word = original_message.text
            existing_word = await chatai.find_one({"word": word})
            if not existing_word:
                word_data = {"word": word}
                await chatai.insert_one(word_data)
                replies_cache.append(word_data)
                
    except Exception as e:
        print(f"Error in save_text: {e}")

async def save_reply(original_message: Message, reply_message: Message):
    global replies_cache, new_replies_cache
    try:
        reply_data = {}

        if original_message.sticker:
            word_id = original_message.sticker.file_id
        elif original_message.photo:
            word_id = original_message.photo.file_id
        elif original_message.video:
            word_id = original_message.video.file_id
        elif original_message.audio:
            word_id = original_message.audio.file_id
        elif original_message.animation:
            word_id = original_message.animation.file_id
        elif original_message.voice:
            word_id = original_message.voice.file_id
        elif original_message.text:
            word_id = original_message.text
        else:
            word_id = None  

        if word_id:
            
            if reply_message.sticker:
                reply_data = {
                    "word": word_id,
                    "text": reply_message.sticker.file_id,
                    "check": "sticker",
                }
                await storeai.insert_one(reply_data)
                new_replies_cache.append(reply_data)
                

            elif reply_message.photo:
                reply_data = {
                    "word": word_id,
                    "text": reply_message.photo.file_id,
                    "check": "photo",
                }
                await storeai.insert_one(reply_data)
                new_replies_cache.append(reply_data)


            elif reply_message.video:
                reply_data = {
                    "word": word_id,
                    "text": reply_message.video.file_id,
                    "check": "video",
                }
                await storeai.insert_one(reply_data)
                new_replies_cache.append(reply_data)
                

            elif reply_message.audio:
                reply_data = {
                    "word": word_id,
                    "text": reply_message.audio.file_id,
                    "check": "audio",
                }
                await storeai.insert_one(reply_data)
                new_replies_cache.append(reply_data)
                

            elif reply_message.animation:
                reply_data = {
                    "word": word_id,
                    "text": reply_message.animation.file_id,
                    "check": "gif",
                }
                await storeai.insert_one(reply_data)
                new_replies_cache.append(reply_data)
                
            elif reply_message.voice:
                reply_data = {
                    "word": word_id,
                    "text": reply_message.voice.file_id,
                    "check": "voice",
                }
                await storeai.insert_one(reply_data)
                new_replies_cache.append(reply_data)
                

            elif reply_message.text:
                reply_data = {
                    "word": word_id,
                    "text": reply_message.text,
                    "check": "text",
                }
                await storeai.insert_one(reply_data)
                new_replies_cache.append(reply_data)
                print("Text reply saved:", reply_data)

    except Exception as e:
        print(f"Error in save_reply: {e}")



async def load_replies_cache():
    global replies_cache, new_replies_cache
    try:
        
        chatai_data = await chatai.find().to_list(length=None)
        replies_cache = [
            {
                "word": reply_data["word"],
                "text": reply_data["text"],
                "check": reply_data["check"]
            }
            for reply_data in chatai_data
            if "word" in reply_data and "text" in reply_data and "check" in reply_data
        ]

        
        storeai_data = await storeai.find().to_list(length=None)
        new_replies_cache = [
            {
                "word": reply_data["word"],
                "text": reply_data["text"],
                "check": reply_data["check"]
            }
            for reply_data in storeai_data
            if "word" in reply_data and "text" in reply_data and "check" in reply_data
        ]

    except Exception as e:
        print(f"Error loading replies cache: {e}")


async def update_replies_database():
    batch_size = 10
    try:
        while True:
            words_cursor = chatai.find({}).limit(batch_size)
            words_batch = await words_cursor.to_list(length=batch_size)
            
            if not words_batch:
                break

            prompt = "text:-\n"
            for i, word_data in enumerate(words_batch, start=1):
                prompt += f"Word{i} = ({word_data['word']})\n"
            prompt += """
            text me jo jo 10 message hai vo sare 10 message ke liye separately Ekdam chatty aur chhota reply do jitna chhota se chhota reply me kam ho jaye utna hi chota reply generate kro, yad rakhna ki tum ek telegram chatbot ho aur sab members log se group me friendly bat krte ho, agar jyada bada reply dena ho to maximum 1 line ka dena barna kosis krna chhota sa chhota reply ho aur purane jaise reply mat dena new reply lagna chahiye aur reply mazedar aur simple ho. Jis language mein yeh text hai, usi official language mein reply karo taki simple se simple translator translate kar sake reply ko. Agar sirf emoji hai toh bas usi se related emoji bhejo. Dhyaan rahe tum ek ladki ho toh reply bhi ladki ke jaise masti bhara ho.

            Bas reply hi likh ke do, kuch extra nahi aur jitna fast ho sake utna fast reply do! aur yrr please hindi me sirf nhi reply ko likho balki text jis lang me bola ja rha hai usi official lang me aur usi text me har reply do yr please barna nhi samjh aata hai. 

            Aur reply bas ish format me likh ke do aur kuch extra nhi:

            Reply1 = "yaha pe word1 ka reply"
            Reply2 = "yaha pe word2 ka reply"
            Reply3 = "yaha pe word3 ka reply"
            Reply4 = "yaha pe word4 ka reply"
            Reply5 = "yaha pe word5 ka reply"
            Reply6 = "yaha pe word6 ka reply"
            Reply7 = "yaha pe word7 ka reply"
            Reply8 = "yaha pe word8 ka reply"
            Reply9 = "yaha pe word9 ka reply"
            Reply10 = "yaha pe word10 ka reply"
            """

            replies = await generate_batch_reply(prompt)

            tasks = []
            for i, word_data in enumerate(words_batch, start=1):
                word = word_data["word"]
                reply = replies.get(f"Reply{i}", "")
                task = save_new_reply(word, reply)
                tasks.append(task)
                
            await asyncio.gather(*tasks)
            
            await asyncio.sleep(5)

    except Exception as e:
        print(f"Error in update_replies_database: {e}")


async def generate_batch_reply(user_input):
    try:
        response = api.gemini(user_input)
        await asyncio.sleep(2)
        if response and "results" in response:
            results = response["results"].splitlines()
            reply_dict = {}
            for line in results:
                if "=" in line:
                    key, value = line.split("=", 1)
                    reply_dict[key.strip()] = value.strip()
            return reply_dict

        from TheApi import api as a
        url_pattern = re.compile(r'(https?://\S+)')
        
        results = a.chatgpt(user_input)
        await asyncio.sleep(10)
        if results and not url_pattern.search(results):
            reply_dict = {}
            for line in results.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    reply_dict[key.strip()] = value.strip()
            return reply_dict
        
        await asyncio.sleep(10)
        return await generate_batch_reply(user_input)

    except Exception as e:
        print("Both ChatGPT APIs failed, retrying in 10 seconds...")
        await asyncio.sleep(10)
        return await generate_batch_reply(user_input)


async def save_new_reply(word, reply):
    try:
        reply_data = {
            "word": word,
            "text": reply,
            "check": "text"
        }

        is_chat = await storeai.find_one({"word": word})
        if not is_chat:
            await storeai.insert_one(reply_data)
            await chatai.delete_one({"word": word})
        else:
            print(f"Reply for {word} already exists in storeai.")

    except Exception as e:
        print(f"Error in save_new_reply for {word}: {e}")


async def continuous_update():
    await load_replies_cache()
    while True:
        try:           
            await update_replies_database()
        except Exception as e:
            print(f"Error in continuous_update: {e}")
        await asyncio.sleep(5)

asyncio.create_task(continuous_update())
