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
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from VampireMusic import app

def upload_file(file_path):
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload", "json": "true"}
    with open(file_path, "rb") as file:
        response = requests.post(url, data=data, files={"fileToUpload": file})
    if response.status_code == 200:
        return True, response.text.strip()
    else:
        return False, f"Error: {response.status_code} - {response.text}"

@app.on_message(filters.command(["tgm", "tm", "telegraph", "tl"]))
async def get_link_group(client, message):
    if not message.reply_to_message:
        return await message.reply_text(
            "⚠️ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ ᴛᴏ ᴜᴘʟᴏᴀᴅ."
        )

    media = message.reply_to_message
    file_size = 0

    if media.photo:
        file_size = media.photo.file_size
    elif media.video:
        file_size = media.video.file_size
    elif media.document:
        file_size = media.document.file_size

    if file_size == 0:
        return await message.reply_text("⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴅᴏᴇsɴ'ᴛ ᴄᴏɴᴛᴀɪɴ ᴀɴʏ ᴅᴏᴡɴʟᴏᴀᴅᴀʙʟᴇ ᴍᴇᴅɪᴀ.")

    if file_size > 200 * 1024 * 1024:
        return await message.reply_text("⚠️ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ ᴜɴᴅᴇʀ 200MB.")

    text = await message.reply("🔄 ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ғɪʟᴇ...")

    async def progress(current, total):
        try:
            await text.edit_text(f"ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ... {current * 100 / total:.1f}%")
        except Exception:
            pass

    try:
        local_path = await media.download(progress=progress)

        if not os.path.exists(local_path):
            return await text.edit_text("❌ Failed to download the media.")

        await text.edit_text("ᴜᴘʟᴏᴀᴅᴇᴅ ᴛᴏ ᴄᴀᴛʙᴏx...")

        success, result = upload_file(local_path)

        if success:
            await message.reply_photo(
                local_path,
                caption=f"✨ {message.from_user.mention(style='md')}, this is your uploaded media!",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴘʜ ʟɪɴᴋ", url=result)]]
                ),
            )
        else:
            await text.edit_text(f"❌ ᴜᴘʟᴏᴀᴅ ғᴀɪʟᴇᴅ!\nError: {result}")

    except Exception as e:
        await text.edit_text(f"❌ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ:\n{e}")

    finally:
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
        except Exception:
            pass
