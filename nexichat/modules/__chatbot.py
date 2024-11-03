import random
from pymongo import InsertOne
import asyncio
import re
from MukeshAPI import api
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.errors import MessageEmpty
from pyrogram.enums import ChatAction, ChatMemberStatus as CMS
from pyrogram.errors.exceptions.flood_420 import SlowmodeWait
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



async def get_chat_language(chat_id):
    try:
        chat_lang = await lang_db.find_one({"chat_id": chat_id})
        return chat_lang["language"] if chat_lang else "en"
    except Exception as e:
        print(f"Error in get_chat_language: {e}")
        return "en"

@nexichat.on_message(filters.incoming)
async def chatbot_response(client: Client, message: Message):
    global blocklist, message_counts
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

        # Check chatbot status
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
            try:
                await generate_reply_and_send(message)

            except SlowmodeWait as e:
                return
            except Exception as e:
                return
        # Save replies if the message is a response
        if message.reply_to_message:
            await save_reply(message.reply_to_message, message)

        if message.text:
            await save_text(message)

    except Exception as e:
        await message.reply_text("🙄🙄")
        print(f"Error in chatbot_response: {e}")

            

async def get_reply_text(message_text):
    global replies_cache, new_replies_cache
    try:
        # Check if reply is cached
        for reply_data in new_replies_cache:
            if reply_data["word"] == message_text:
                return reply_data["text"], reply_data["check"]
        
        # Check in the database if not in cache
        reply_data = await storeai.find_one({"word": message_text})
        if reply_data:
            new_replies_cache.append(reply_data)
            return reply_data["text"], reply_data["check"]
        
        # Fallback to random reply from cache
        if new_replies_cache:
            random_reply = random.choice(new_replies_cache)
            return random_reply["text"], random_reply["check"]
        
        # Load cache if empty
        await load_replies_cache()
        return None, None
    except Exception as e:
        print(f"Error in get_reply: {e}")
        return None, None


async def save_text(original_message: Message):
    global replies_cache
    try:
        if original_message.text:
            word = original_message.text
            if not await chatai.find_one({"word": word}):
                word_data = {"word": word}
                await chatai.insert_one(word_data)
                replies_cache.append(word_data)
                
    except Exception as e:
        print(f"Error in save_text: {e}")



async def save_reply(original_message: Message, reply_message: Message):
    global new_replies_cache
    try:
        # Only save original messages that are NOT text
        if any([original_message.sticker, original_message.photo, original_message.video, 
                original_message.audio, original_message.voice, original_message.animation]):
            reply_data = {
                "original_word": original_message.sticker.file_id if original_message.sticker else 
                                original_message.photo.file_id if original_message.photo else 
                                original_message.video.file_id if original_message.video else 
                                original_message.audio.file_id if original_message.audio else 
                                original_message.voice.file_id if original_message.voice else 
                                original_message.animation.file_id,
                "original_type": "sticker" if original_message.sticker else 
                                "photo" if original_message.photo else 
                                "video" if original_message.video else 
                                "audio" if original_message.audio else 
                                "voice" if original_message.voice else 
                                "gif",
                "replies": []
            }

            # Prepare the reply based on the format of the reply message
            if reply_message.sticker:
                reply_data["replies"].append({"text": reply_message.sticker.file_id, "check": "sticker"})
            elif reply_message.photo:
                reply_data["replies"].append({"text": reply_message.photo.file_id, "check": "photo"})
            elif reply_message.video:
                reply_data["replies"].append({"text": reply_message.video.file_id, "check": "video"})
            elif reply_message.audio:
                reply_data["replies"].append({"text": reply_message.audio.file_id, "check": "audio"})
            elif reply_message.voice:
                reply_data["replies"].append({"text": reply_message.voice.file_id, "check": "voice"})
            elif reply_message.animation:
                reply_data["replies"].append({"text": reply_message.animation.file_id, "check": "gif"})
            elif reply_message.text:
                reply_data["replies"].append({"text": reply_message.text, "check": "text"})

            # Insert or update the original message and its replies in the database
            await storeai.update_one(
                {"original_word": reply_data["original_word"], "original_type": reply_data["original_type"]},
                {"$push": {"replies": {"$each": reply_data["replies"]}}},
                upsert=True
            )

            new_replies_cache.append(reply_data)

    except Exception as e:
        print(f"Error in save_reply: {e}")

async def get_reply(original_message):
    try:
        cached_reply = next(
            (entry for entry in new_replies_cache if entry["original_word"] == original_message.file_id), 
            None
        )
        if not cached_reply:
            cached_reply = await storeai.find_one({"original_word": original_message.file_id})

        if cached_reply and cached_reply.get("replies"):
            return random.choice(cached_reply["replies"])

        return None

    except Exception as e:
        print(f"Error in get_reply: {e}")
        return None

async def generate_reply_and_send(message):
    if message.text:
        reply_data = await get_reply_for_text(message)
        if reply_data:
            response_text = reply_data["text"]
            reply_type = reply_data["check"]
            chat_lang = await get_chat_language(message.chat.id)
            
            if reply_type == "text":
                try:
                    translated_text = response_text if not chat_lang or chat_lang == "nolang" else GoogleTranslator(source='auto', target=chat_lang).translate(response_text)
                except Exception as e:
                    translated_text = response_text
                    print(f"Translation error: {e}")
            else:
                translated_text = response_text

            if reply_type == "text":
                await message.reply_text(translated_text)
            elif reply_type == "sticker":
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
        else:
            await message.reply_text("Koi saved reply nahi mila! for text")
    else:
        reply_data = await get_reply(message)
        if reply_data:
            response_text = reply_data["text"]
            reply_type = reply_data["check"]

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
            else:
                await message.reply_text(response_text)
        else:
            await message.reply_text("Koi saved reply nahi mila!")

async def load_replies_cache():
    global replies_cache, new_replies_cache
    try:
        
        chatai_data = await chatai.find().to_list(length=None)
        replies_cache = [{"word": reply_data["word"], "text": reply_data["text"], "check": reply_data["check"]} for reply_data in chatai_data]

        
        storeai_data = await storeai.find().to_list(length=None)
        new_replies_cache = [{"word": reply_data["word"], "text": reply_data["text"], "check": reply_data["check"]} for reply_data in storeai_data]

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
            text me message hai uske liye Ekdam chatty aur chhota reply do jitna chhota se chhota reply me kam ho jaye utna hi chota reply do agar jyada bada reply dena ho to maximum 1 line ka dena barna kosis krna chhota sa chhota reply ho aur purane jaise reply mat dena new reply lagna chahiye aur reply mazedar aur simple ho. Jis language mein yeh text hai, usi language mein reply karo. Agar sirf emoji hai toh bas usi se related emoji bhejo. Dhyaan rahe tum ek ladki ho toh reply bhi ladki ke jaise masti bhara ho.

            Bas reply hi likh ke do, kuch extra nahi aur jitna fast ho sake utna fast reply do! aur yrr please hindi me sirf nhi reply ko likho balki text jis lang me bola ja rha hai usi lang me aur usi text me har reply do yr please barna nhi samjh aata hai. 

            Aur reply format aisa hona chahiye:

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
                reply = replies.get(f"Reply{i}", "Default reply")
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
        await asyncio.sleep(2)
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

async def get_reply_for_text(word):
    try:
        reply_data = await storeai.find_one({"word": reply_data["word"])
        if reply_data:
            return reply_data["text"], reply_data["check"]

        return None, None

    except Exception as e:
        print(f"Error in get_reply_for_text for {word}: {e}")
        return None, None

async def continuous_update():
    await load_replies_cache()
    while True:
        try:           
            await update_replies_database()
        except Exception as e:
            print(f"Error in continuous_update: {e}")
        await asyncio.sleep(5)

asyncio.create_task(continuous_update())
