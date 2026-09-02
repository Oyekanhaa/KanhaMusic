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

from time import time
from functools import wraps
from pyrogram.types import Message

def rate_limit(wait_time):
    last_clicked_times = {}

    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            user_id = message.from_user.id
            now = time()
            
            if user_id in last_clicked_times and (now - last_clicked_times[user_id] < wait_time):
                await message.edit(f"ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ {int(wait_time - (now - last_clicked_times[user_id]))} sᴇᴄᴏɴᴅs ʙᴇғᴏʀᴇ ᴄʟɪᴄᴋɪɴɢ ᴀɢᴀɪɴ.", show_alert=True)
                return
            
            last_clicked_times[user_id] = now
            return await func(client, message, *args, **kwargs)
        
        return wrapper
    return decorator
