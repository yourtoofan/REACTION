from pyrogram import Client, filters
from pyrogram.types import Message
from nexichat import nexichat as app

@app.on_message(filters.command("history"))
async def fetch_history(client: Client, message: Message):
    try:
        # Extract the number of messages to fetch
        args = message.text.split()
        limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 50
        
        if limit <= 0:
            await message.reply("Please provide a valid number greater than 0.")
            return

        # Get the chat ID (current chat)
        chat_id = message.chat.id

        # Fetch message history
        async for msg in client.get_chat_history(chat_id, limit=limit):
            # Send each message one by one
            await message.reply_text(
                f"Message ID: {msg.message_id}\n"
                f"From: {msg.from_user.first_name if msg.from_user else 'Unknown'}\n"
                f"Text: {msg.text if msg.text else '[Non-text message]'}"
            )
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

