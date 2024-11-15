from pyrogram import Client, filters
from pyrogram.types import Message
from nexichat import nexichat as app, mongo, db
from MukeshAPI import api
from nexichat.modules.helpers import chatai, CHATBOT_ON, languages

lang_db = db.ChatLangDb.LangCollection
message_cache = {}

async def get_chat_language(chat_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else None

@app.on_message(filters.text, group=2)
async def store_messages(client, message: Message):
    global message_cache

    chat_id = message.chat.id
    chat_lang = await get_chat_language(chat_id)

    if not chat_lang:
        if message.from_user and message.from_user.is_bot:
            return

        if chat_id not in message_cache:
            message_cache[chat_id] = []

        message_cache[chat_id].append(message)

        if len(message_cache[chat_id]) >= 10:
            history = "\n\n".join(
                [f"Text: {msg.text}..." for msg in message_cache[chat_id]]
            )
            user_input = f"""
            [
            {history}
            ]

            ye sab upar jitna bhi message hai har text me vo sab ko ek ek ko acha se padh ke samjho ki kon sa lang me bat likha hua hai, ho sakta hai har sentence alag alag lang me likha hoga to tum dekho ki maximum sentence kis lang me likha hai, jis lang ka jyada use hua hai ush official lang ka lang_code do.
            sirf lang code do uske alava kuch nhi.
            """
            response = api.gemini(user_input)
            x = response["results"]
            await message.reply_text(f"Lang code detected for this chat:- {x}")
            message_cache[chat_id].clear()
