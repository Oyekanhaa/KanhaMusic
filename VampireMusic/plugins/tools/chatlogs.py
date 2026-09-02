# -----------------------------------------------
# 🔸 VampireMusic Project
# 🔹 Developed & Maintained by: Vampire Bots (https://github.com/TEAM-VAMPIRE-OP)
# 📅 Copyright © 2025 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by TEAM-VAMPIRE-OP
# -----------------------------------------------


import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import LOGGER_ID as LOG_GROUP_ID
from VampireMusic import app 
from pyrogram.errors import RPCError
from typing import Union, Optional
from PIL import Image, ImageDraw, ImageFont
import asyncio, os, aiohttp
from pathlib import Path
from pyrogram.enums import ParseMode

photo = [
    "https://files.catbox.moe/tdj8he.jpg",
    "https://files.catbox.moe/ygpszq.jpg",
    
]  


@app.on_message(filters.new_chat_members, group=2)
async def join_watcher(_, message):    
    chat = message.chat
    link = await app.export_chat_invite_link(message.chat.id)
    for members in message.new_chat_members:
        if members.id == app.id:
            count = await app.get_chat_members_count(chat.id)

            msg = (
                f"#𝗕𝗢𝗧_𝗔𝗗𝗗𝗘𝗗_𝗡𝗘𝗪_𝗚𝗥𝗢𝗨𝗣\n\n"
                f"⦿───────────────────⦿\n\n"
                f"◎ ᴄʜᴀᴛ ɴᴀᴍᴇ ▸ {message.chat.title}\n"
                f"◎ ᴄʜᴀᴛ ɪᴅ ▸ {message.chat.id}\n"
                f"◎ ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ ▸ @{message.chat.username}\n"
                f"◎ ᴄʜᴀᴛ ʟɪɴᴋ ▸ [ᴄʟɪᴄᴋ]({link})\n"
                f"◎ ɢʀᴏᴜᴘ ᴍᴇᴍʙᴇʀs ▸ {count}\n"
                f"◎ ᴀᴅᴅᴇᴅ ʙʏ ▸ {message.from_user.mention}\n"
    f"⦿───────────────────⦿"
            )
            await app.send_photo(LOG_GROUP_ID, photo=random.choice(photo), caption=msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"#𝗚𝗥𝗢𝗨𝗣 #𝗟𝗜𝗡𝗞", url=f"{link}")]
         ]))



@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    if (await app.get_me()).id == message.left_chat_member.id:
        remove_by = message.from_user.mention if message.from_user else "𝐔ɴᴋɴᴏᴡɴ 𝐔sᴇʀ"
        title = message.chat.title
        username = f"@{message.chat.username}" if message.chat.username else "𝐏ʀɪᴠᴀᴛᴇ 𝐂ʜᴀᴛ"
        chat_id = message.chat.id
        left = f"✫ <b><u>#𝗟𝗘𝗙𝗧_𝗚𝗥𝗢𝗨𝗣</u></b> ✫\n\nᴄʜᴀᴛ ᴛɪᴛʟᴇ : {title}\n\nᴄʜᴀᴛ ɪᴅ : {chat_id}\n\nʀᴇᴍᴏᴠᴇᴅ ʙʏ : {remove_by}\n\nʙᴏᴛ : @{app.username}"
        await app.send_photo(LOG_GROUP_ID, photo=random.choice(photo), caption=left)
