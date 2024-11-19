from pyrogram import Client, filters
from pyrogram.types import Message
from nexichat import nexichat as app
from config import API_ID, API_HASH


@app.on_message(filters.command("generate"))
async def generate_string_session(client: Client, message: Message):
    chat_id = message.chat.id

    try:
        # Ask for phone number
        await message.reply("Send your phone number (with country code):")
        response = await client.listen(chat_id, timeout=300)  # Wait for the user's response (5 minutes timeout)
        phone = response.text.strip()

        # Initialize user client
        user_client = Client("user_session", api_id=API_ID, api_hash=API_HASH)

        await user_client.connect()

        # Send the login code
        await user_client.send_code(phone_number=phone)
        await message.reply("Please check your Telegram account for the login code and send it here:")
        code_response = await client.listen(chat_id, timeout=300)  # Wait for code input
        code = code_response.text.strip()

        # Try signing in with the code
        try:
            await user_client.sign_in(phone_number=phone, code=code)
        except Exception:
            # Ask for two-step password if required
            await message.reply("Enter your two-step verification password:")
            password_response = await client.listen(chat_id, timeout=300)
            password = password_response.text.strip()
            await user_client.check_password(password=password)

        # Generate string session
        string_session = await user_client.export_session_string()
        await message.reply(
            f"Here is your Pyrogram string session:\n\n`{string_session}`\n\nKeep it safe!"
        )

    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")

    finally:
        # Disconnect the user client safely
        if 'user_client' in locals():
            await user_client.disconnect()
