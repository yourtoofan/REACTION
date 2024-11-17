from pyrogram import Client, filters
import logging
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
from nexichat import db as mongodb, nexichat
from config import API_ID, API_HASH, OWNER_ID

clonebotdb = mongodb.clonebotdb
IDCLONES = set()

@Client.on_message(filters.command("idclone"))
async def idclone_txt(client, message):
    if len(message.command) > 1:
        string_session = message.text.split(" ", 1)[1].strip()
        mi = await message.reply_text("**Checking the string session...**")
        try:
            ai = Client(
                string_session, 
                api_id=API_ID, 
                api_hash=API_HASH, 
                plugins=dict(root="nexichat/idchatbot")
            )
            await ai.start()
            user = await ai.get_me()
            user_id = user.id
            
            # Check if already cloned
            cloned_user = await clonebotdb.find_one({"string_session": string_session})
            if cloned_user:
                await mi.edit_text("**🤖 This chatbot session is already cloned ✅**")
                return
            
            # Save clone details
            details = {
                "user_id": user_id,
                "is_user": True,
                "name": user.first_name,
                "string_session": string_session,
                "username": user.username or "No username",
            }
            await clonebotdb.insert_one(details)
            IDCLONES.add(user_id)
            
            await mi.edit_text(
                f"**Chatbot with session `{user_id}` cloned successfully ✅.**\n"
                f"**Remove clone with:** /delidclone `{string_session}`\n"
                f"**List all cloned sessions with:** /clonedid"
            )
        except (AccessTokenExpired, AccessTokenInvalid):
            await mi.edit_text("**Invalid string session. Please provide a valid one.**")
        except Exception as e:
            logging.exception("Error while cloning chatbot.")
            await mi.edit_text(f"⚠️ <b>Error:</b> `{e}`\n\n**Contact support if needed.**")
    else:
        await message.reply_text("**Provide a valid string session after the /idclone command.**")


@Client.on_message(filters.command("clonedid"))
async def list_cloned_chatbots(client, message):
    try:
        cloned_chatbots = clonebotdb.find()
        cloned_list = await cloned_chatbots.to_list(length=None)
        if not cloned_list:
            await message.reply_text("**No id-chatbots have been cloned yet.**")
            return
        total_clones = len(cloned_list)
        text = f"**Total Cloned Chatbots:** {total_clones}\n\n"
        for bot in cloned_list:
            text += f"**User ID:** `{bot['user_id']}`\n"
            text += f"**Name:** {bot['name']}\n"
            text += f"**Username:** @{bot['username']}\n\n"
        await message.reply_text(text)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("**An error occurred while listing cloned chatbots.**")


@Client.on_message(filters.command("delidclone"))
async def delete_cloned_chatbot(client, message):
    if len(message.command) < 2:
        await message.reply_text("**⚠️ Please provide the string session after the command.**")
        return
    try:
        string_session = " ".join(message.command[1:])
        ok = await message.reply_text("**Checking the string session...**")
        
        cloned_user = await clonebotdb.find_one({"string_session": string_session})
        if cloned_user:
            await clonebotdb.delete_one({"string_session": string_session})
            await ok.edit_text(
                f"**🤖 Your cloned chatbot has been removed from my database ✅**\n"
                f"**🔄 Kindly revoke your session token if no longer in use.**"
            )
        else:
            await message.reply_text("**⚠️ The provided string session is not in the cloned list.**")
    except Exception as e:
        logging.exception(e)
        await message.reply_text(f"**An error occurred while deleting the cloned chatbot:** {e}")


@Client.on_message(filters.command("delallidclone") & filters.user(int(OWNER_ID)))
async def delete_all_cloned_chatbots(client, message):
    try:
        a = await message.reply_text("**Deleting all cloned chatbots...**")
        await clonebotdb.delete_many({})
        IDCLONES.clear()
        await a.edit_text("**All cloned chatbots have been deleted successfully ✅**")
    except Exception as e:
        await a.edit_text(f"**An error occurred while deleting all cloned chatbots.** {e}")
        logging.exception(e)
