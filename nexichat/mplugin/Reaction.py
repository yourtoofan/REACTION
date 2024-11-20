from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.incoming, group=5)
async def react_to_messages(client: Client, message: Message):
    try:
        await client.react(message.chat.id, message.id, "👍")
    except Exception as e:
        print(f"Failed to react to message: {e}")

