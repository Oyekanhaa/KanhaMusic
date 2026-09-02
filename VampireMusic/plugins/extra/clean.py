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


import os
import shutil
from pyrogram import filters
from VampireMusic import app
from VampireMusic.misc import SUDOERS


@app.on_message(filters.command("clean") & SUDOERS)
async def clean(_, message):
    A = await message.reply_text("ᴄʟᴇᴀɴɪɴɢ ᴛᴇᴍᴘ ᴅɪʀᴇᴄᴛᴏʀɪᴇs...")
    dir = "downloads"
    dir1 = "cache"
    shutil.rmtree(dir)
    shutil.rmtree(dir1)
    os.mkdir(dir)
    os.mkdir(dir1)
    await A.edit("ᴛᴇᴍᴘ ᴅɪʀᴇᴄᴛᴏʀɪᴇs ᴀʀᴇ ᴄʟᴇᴀɴᴇᴅ")
