from pyrogram import Client, filters
from pyrogram.types import Message
from nexichat import nexichat as app

message_cache = {}

@app.on_message(filters.text, group=2)
async def store_messages(client, message: Message):
    global message_cache

    chat_id = message.chat.id

    # Ignore bot messages
    if message.from_user and message.from_user.is_bot:
        return

    # Initialize cache for the chat if not already present
    if chat_id not in message_cache:
        message_cache[chat_id] = []

    # Add the new message to the cache
    message_cache[chat_id].append(message)

    # Check if cache has reached 10 messages
    if len(message_cache[chat_id]) >= 10:
        # Create a reply with the last 10 messages
        history = "\n\n".join(
            [
                f"Message ID: {msg.id}\nText: {msg.text[:50]}..."  # Truncated for safety
                for msg in message_cache[chat_id]
            ]
        )
        
        try:
            # Send the history
            await message.reply(f"Last 10 messages in this chat:\n\n{history}")
        except Exception as e:
            print(f"Failed to send reply: {e}")

        # Clear the cache for this chat
        message_cache[chat_id].clear()
