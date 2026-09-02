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


from pyrogram import Client, filters
import requests
import random
from VampireMusic import app

UNSPLASH_ACCESS_KEY = "oBw-gH0Pt6e4SqjhTM65yYOrlIGgz-Jrnj8WjCZIn_0"
UNSPLASH_QUERY = "Yo Yo Honey Singh"

@app.on_message(filters.command("random") & filters.private)
async def send_random_image(client, message):
    url = f"https://api.unsplash.com/search/photos?page=1&query={UNSPLASH_QUERY}&client_id={UNSPLASH_ACCESS_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            random_image = random.choice(data["results"])["urls"]["full"]
            await message.reply_photo(random_image, caption="ʜᴇʀᴇ ɪs a ʀᴀɴᴅᴏᴍ ɪᴍᴀɢᴇ ғᴏʀ ʏᴏᴜ!")
        else:
            await message.reply_text("ɴᴏ ɪᴍᴀɢᴇs ғᴏᴜɴᴅ ғᴏʀ ᴛʜᴇ ǫᴜᴇʀʏ.")
    else:
        await message.reply_text("ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ɪᴍᴀɢᴇs. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")
