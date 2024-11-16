from pyrogram import Client, filters
from pyrogram.types import Message
from nexichat import nexichat as app, mongo, db
from MukeshAPI import api
from nexichat.modules.helpers import chatai, CHATBOT_ON, languages
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

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

        if len(message_cache[chat_id]) >= 30:
            history = "\n\n".join(
                [f"Text: {msg.text}..." for msg in message_cache[chat_id]]
            )
            user_input = f"""
            ye sare messages kon sa lang me likha gya hai ho sakta hai kuch sentences ka lang alag hoga tum overall dekhkho to kon sa lang me jyada tar messages hai.
            overall sare messages ka lang detect krke anylise krke mujhe bas lang name aur sath me ush lang ka code provide kro aur kuch nhi.
            ye rha niche sara sentences :-
            
            {history}
            """

            response = api.gemini(user_input)
            x = response["results"]
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("sᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ", callback_data="choose_lang")]])    
            await message.reply_text(f"**Chat language detected for this chat:**\n\n{history}\n\n**You can set my lang by /lang**", reply_markup=reply_markup)
            message_cache[chat_id].clear()
