# -----------------------------------------------
# 🔸 KanhaMusic Project
# 🔹 Developed & Maintained by: Anu Bots (https://github.com/TEAM-VAMPIRE-OP)
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


from pyrogram import Client, filters
from pyrogram.types import Message, ChatMember
import logging
from KanhaMusic import app

logging.basicConfig(level=logging.INFO)

@app.on_message(filters.video_chat_started)
async def video_chat_started(client, message: Message):
    chat = message.chat
    await message.reply(
        f"🎥 ᴠɪᴅᴇᴏ ᴄʜᴀᴛ ʜᴀs sᴛᴀʀᴛᴇᴅ ɪɴ {chat.title}!\n\n ᴊᴏɪɴ ᴜs ɴᴏᴡ ғᴏʀ ᴀ ғᴜɴ ᴛɪᴍᴇ ᴛᴏɢᴇᴛʜᴇʀ! 😄"
    )

@app.on_message(filters.video_chat_ended)
async def video_chat_ended(client, message: Message):
    chat = message.chat
    await message.reply(
        f"🚫 ᴠɪᴅᴇᴏ ᴄʜᴀᴛ ʜᴀs ᴇɴᴅᴇᴅ ɪɴ {chat.title}.\n\nsᴇᴇ ʏᴏᴜ ɴᴇxᴛ ᴛɪᴍᴇ! 👋"
    )