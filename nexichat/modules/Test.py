from pyrogram import Client, filters
from pyrogram.types import Message
from nexichat import nexichat as app

from pyrogram import Client, filters


message_cache = {}

@app.on_message(filters.text, group=2)
async def store_messages(client, message):
    global message_cache

    chat_id = message.chat.id

    # Initialize cache for the chat if not already present
    if chat_id not in message_cache:
        message_cache[chat_id] = []

    # Add the new message to the cache
    message_cache[chat_id].append(message)

    # Check if cache has reached 10 messages
    if len(message_cache[chat_id]) >= 10:
        # Create a reply with the last 10 messages
        history = "\n\n".join(
            [f"Message ID: {msg.message_id}\nText: {msg.text}" for msg in message_cache[chat_id]]
        )
        
        # Send the history
        await message.reply(f"Last 10 messages in this chat:\n\n{history}")
        
        # Clear the cache for this chat
        message_cache[chat_id].clear()

