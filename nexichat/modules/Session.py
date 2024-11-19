from pyrogram import Client, filters
from pyrogram.types import Message
from nexichat import nexichat as app
from config import API_ID, API_HASH

@app.on_message(filters.command("generate"))
async def generate_string_session(client: Client, message: Message):
    chat_id = message.chat.id
    await client.ask(chat_id, "Send your phone number (with country code):")
    phone = response.text

    user_client = Client("user_session", api_id=API_ID, api_hash=API_HASH)
    
    try:
        await user_client.connect()
        await user_client.send_code(phone_number=phone)
        await client.ask(chat_id, "Please check your Telegram account for the login code and send it here:")
        code = response.text

        try:
            await user_client.sign_in(phone_number=phone, code=code)
        except Exception:
            await client.ask(chat_id, "Enter your two-step verification password:")
            password = response.text
            await user_client.check_password(password=password)

        string_session = await user_client.export_session_string()
        await message.reply(f"Here is your Pyrogram string session:\n\n`{string_session}`\n\nKeep it safe!")
    
    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")
    
    finally:
        await user_client.disconnect()
