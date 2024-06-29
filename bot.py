import os
import math
import logging
from datetime import date, datetime 
import pytz
import pytz
from typing import Union, Optional, AsyncGenerator

from aiohttp import web
from pyrogram import Client, types
from pyrogram.errors import BadRequest, Unauthorized

from database.ia_filterdb import Media
from database.users_chats_db import db
from info import API_ID, API_HASH, BOT_TOKEN, LOG_CHANNEL, UPTIME, PORT
from utils import temp
from plugins import web_server
from Script import script 

import logging
import logging.config
import asyncio

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Professor-Bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=10,
        )

    async def start(self):
        await super().start()
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.id = me.id
        self.mention = me.mention
        self.uptime = UPTIME
        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        time = now.strftime("%H:%M:%S %p")
        await self.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(a=today, b=time, c=temp.U_NAME))
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

        await self.send_report_message()
    
    async def send_report_message(self):
        while True:
            tz = pytz.timezone('Asia/Kolkata')
            today = date.today()
            now = datetime.now(tz)
            formatted_date_1 = now.strftime("%d-%B-%Y")
            formatted_date_2 = today.strftime("%d %b")
            time = now.strftime("%H:%M:%S %p")

            total_users = await db.total_users_count()
            total_chats = await db.total_chat_count()
            today_users = await db.daily_users_count(today) + 1
            today_chats = await db.daily_chats_count(today) + 1

            if now.hour == 23 and now.minute == 59:
                k = await self.send_message(
                    chat_id=LOG_CHANNEL,
                    text=script.REPORT_TXT.format(
                        a=formatted_date_1,
                        b=formatted_date_2,
                        c=time,
                        d=total_users,
                        e=total_chats,
                        f=today_users,
                        g=today_chats,
                        h=temp.U_NAME
                    )
                )
                await k.pin()
                # Sleep for 1 minute to avoid sending multiple messages
                await asyncio.sleep(60)
            else:
                # Sleep for 1 minute and check again
                await asyncio.sleep(60)

    async def stop(self, *args):
        await super().stop()
        me = await self.get_me()
        logger.info(f"{me.first_name} is restarting...")

    async def iter_messages(self, chat_id: Union[int, str], limit: int, offset: int = 0) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1

app = Bot()
app.run()
