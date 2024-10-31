import random
from pyrogram import Client, filters
from pyrogram.errors import MessageEmpty
from pyrogram.enums import ChatAction
from pyrogram.types import Message
from nexichat.database.chats import add_served_chat
from nexichat.database.users import add_served_user
from TheApi import api
from nexichat import db
from nexichat import nexichat

status_db = db.chatbot_status_db.status
chatai = db.Word.WordDb

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
                user_input = f"""
                Input: {message.text}
                
                You are a friendly and concise chatbot designed to reply with short, context-aware responses. Please respond in the same language as the input text, keeping replies as short as possible (no longer than one sentence). If the input is in the form of a simple emoji, reply with a single related emoji.
                Instructions:
                1. Use a tone that feels casual and natural, like a female friend.
                2. Keep responses direct, limited to the essential idea of the input, and only elaborate if necessary.
                3. If a reply can be simplified, prioritize making it as short as possible.
                4. If an input message has any gender-specific tone or phrasing, reply in a way that keeps the tone friendly and light-hearted.
                
                Now Reply concisely to the following text without adding anything extra. Just give the reply only.
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
