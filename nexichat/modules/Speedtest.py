import asyncio
import speedtest
from pyrogram import filters
from pyrogram.types import Message
from nexichat import nexichat


server_result_template = (
    "✯ <b>sᴩᴇᴇᴅᴛᴇsᴛ ʀᴇsᴜʟᴛs</b> ✯\n\n"
    "<u><b>ᴄʟɪᴇɴᴛ :</b></u>\n"
    "<b>» ɪsᴩ :</b> {isp}\n"
    "<b>» ᴄᴏᴜɴᴛʀʏ :</b> {country}\n\n"
    "<u><b>sᴇʀᴠᴇʀ :</b></u>\n"
    "<b>» ɴᴀᴍᴇ :</b> {server_name}\n"
    "<b>» ᴄᴏᴜɴᴛʀʏ :</b> {server_country}, {server_cc}\n"
    "<b>» sᴩᴏɴsᴏʀ :</b> {sponsor}\n"
    "<b>» ʟᴀᴛᴇɴᴄʏ :</b> {latency} ms\n"
    "<b>» ᴩɪɴɢ :</b> {ping} ms"
)

def run_speedtest():
    test = speedtest.Speedtest()
    test.get_best_server()
    test.download()
    test.upload()
    results = test.results.dict()
    return results

@nexichat.on_message(filters.command(["speedtest", "spt"], prefixes=["/"]))
async def speedtest_function(client, message: Message):
    m = await message.reply_text("**ʀᴜɴɴɪɴɢ ꜱᴩᴇᴇᴅ...**")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_speedtest)

        output = server_result_template.format(
            isp=result["client"]["isp"],
            country=result["client"]["country"],
            server_name=result["server"]["name"],
            server_country=result["server"]["country"],
            server_cc=result["server"]["cc"],
            sponsor=result["server"]["sponsor"],
            latency=result["server"]["latency"],
            ping=result["ping"],
        )

        # Send result with photo
        msg = await message.reply_photo(
            photo=result["share"], caption=output, parse_mode="html"
        )
        await m.delete()
    except Exception as e:
        await m.edit_text(f"**Error:** `{e}`")
