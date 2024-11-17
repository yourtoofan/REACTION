import asyncio
from os import getenv

from dotenv import load_dotenv
from pyrogram import Client

load_dotenv()
from dotenv import load_dotenv

import config


assistants = []
assistantids = []


class Userbot(Client):
    def __init__(self):
        self.one = Client(
            name="VIPAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=False,
            plugins=dict(root="VIPMUSIC.plugins.USERBOT"),
        )
        

    async def start(self):
        LOGGER(__name__).info(f"Starting Assistants...")

        if config.STRING1:
            await self.one.start()
            try:
                await self.one.join_chat("THE_VIP_BOY")
                await self.one.join_chat("THE_VIP_BOY_OP")
                await self.one.join_chat("TG_FRIENDSS")
                await self.one.join_chat("VIP_CREATORS")
                await self.one.join_chat("TheTeamVivek")

            except:
                pass
            assistants.append(1)
            try:
                await self.one.send_message(config.int(OWNER_ID), "ᴀssɪsᴛᴀɴᴛ sᴛᴀʀᴛᴇᴅ !")
                
            except Exception as e:
                print(f"{e}")

            self.one.id = self.one.me.id
            self.one.name = self.one.me.from 
            self.one.username = self.one.me.username
            assistantids.append(self.one.id)
            LOGGER(__name__).info(f"Assistant Started as {self.one.me.first_name}")

        
      

    async def stop(self):
        LOGGER(__name__).info(f"Stopping Assistants...")
        try:
            if config.STRING1:
                await self.one.stop()
        except:
            pass
