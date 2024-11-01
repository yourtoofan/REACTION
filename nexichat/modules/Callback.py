from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup
from nexichat import nexichat, LOGGER, db
from nexichat.modules.helpers import (
    HELP_READ, HELP_BTN, ABOUT_READ, ABOUT_BTN, BACK, START, DEV_OP, SOURCE_READ
)

lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status

@nexichat.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    LOGGER.info(query.data)
    data = query.data

    if data == "HELP":
        await query.message.edit_text(
            text=HELP_READ,
            reply_markup=InlineKeyboardMarkup(HELP_BTN),
            disable_web_page_preview=True,
        )

    elif data == "CLOSE":
        await query.message.delete()
        await query.answer("Closed menu!", show_alert=True)

    elif data == "BACK":
        await query.message.edit(
            text=START,
            reply_markup=InlineKeyboardMarkup(DEV_OP),
        )

    elif data == "SOURCE":
        await query.message.edit(
            text=SOURCE_READ,
            reply_markup=InlineKeyboardMarkup(BACK),
            disable_web_page_preview=True,
        )

    elif data.startswith("setlang_"):
        lang_code = data.split("_")[1]
        chat_id = query.message.chat.id
        if lang_code in languages.values():
            lang_db.update_one({"chat_id": chat_id}, {"$set": {"language": lang_code}}, upsert=True)
            await query.answer(f"Language set to {lang_code.title()}.", show_alert=True)
            await query.message.edit_text(f"Language set to {lang_code.title()}.")
        else:
            await query.answer("Invalid language selection.", show_alert=True)

    elif data == "enable_chatbot":
        chat_id = query.message.chat.id
        status_db.update_one({"chat_id": chat_id}, {"$set": {"status": "enabled"}}, upsert=True)
        await query.answer("Chatbot enabled ✅", show_alert=True)
        await query.edit_message_text(
            f"Chat: {query.message.chat.title}\n**Chatbot enabled.**"
        )

    elif data == "disable_chatbot":
        chat_id = query.message.chat.id
        status_db.update_one({"chat_id": chat_id}, {"$set": {"status": "disabled"}}, upsert=True)
        await query.answer("Chatbot disabled!", show_alert=True)
        await query.edit_message_text(
            f"Chat: {query.message.chat.title}\n**Chatbot disabled.**"
        )
