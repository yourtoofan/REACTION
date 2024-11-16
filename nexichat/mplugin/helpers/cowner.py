from nexichat import CLONE_OWNERS, get_clone_owner
from config import OWNER_ID

async def is_owner(client, user_id):
    bot_id = client.me.id
    owner_id = get_clone_owner(bot_id)
    if owner_id == user_id or user_id == OWNER_ID:
        return True
    return "You don't have permission to use this command on this bot."
