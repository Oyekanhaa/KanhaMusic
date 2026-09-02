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

import asyncio
from pyrogram import Client, enums
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import OWNER_ID
from VampireMusic import app

@app.on_message(filters.command(["banall"], prefixes=["/", "!"]))
async def banall_command(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    chat_member = await client.get_chat_member(chat_id, user_id)

    if user_id == OWNER_ID or chat_member.status == enums.ChatMemberStatus.OWNER:
        await message.reply_text(
            "ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴛᴀʀᴛ ᴛʜᴇ ᴅᴀɴᴀʟʟ ᴘʀᴏᴄᴇss? ᴏɴʟʏ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴄᴀɴ ᴀᴘᴘʀᴏᴠᴇ ᴛʜɪs ᴀᴄᴛɪᴏɴ.",
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("ᴀᴘᴘʀᴏᴠᴇ", callback_data="approve_banall"),
                    InlineKeyboardButton("ᴅᴇᴄʟɪɴᴇ", callback_data="decline_banall")
                ]]
            )
        )
    else:
        await message.reply_text("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ. ᴏɴʟʏ ᴛʜᴇ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")

@app.on_callback_query(filters.regex("approve_banall"))
async def approve_banall(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.first_name

    chat_member = await client.get_chat_member(chat_id, user_id)

    if user_id == OWNER_ID or chat_member.status == enums.ChatMemberStatus.OWNER:
        await callback_query.message.edit_text(f"ʙᴀɴᴀʟʟ ꜱᴛᴀʀᴛɪɴɢ ... ᴀᴘᴘʀᴏᴠᴇᴅ ʙʏ {user_name}.")

        bot = await client.get_chat_member(chat_id, client.me.id)
        bot_permission = bot.privileges.can_restrict_members

        if bot_permission:
            ban_count = 0
            async for member in client.get_chat_members(chat_id):
                try:
                    await client.ban_chat_member(chat_id, member.user.id)
                    ban_count += 1
                except Exception:
                    pass
            await callback_query.message.edit_text(f"<b><u>⬤ ʙᴀɴᴀʟʟ ᴘʀᴏᴄᴇss ᴄᴏᴍᴘʟᴇᴛᴇᴅ!</b></u>\n\n<b>● ᴛᴏᴛᴀʟ ᴜsᴇʀs ➠</b> {ban_count}\n<b>● ʙᴀɴɴᴇᴅ ʙʏ ➠</b> {user_name}")
        else:
            await callback_query.message.edit_text("ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴛʜᴇ ʀɪɢʜᴛ ᴛᴏ ʀᴇsᴛʀɪᴄᴛ ᴜsᴇʀs ᴏʀ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ɪɴ sᴜᴅᴏ ᴜsᴇʀs.")
    else:
        await callback_query.message.edit_text(f"{user_name}, ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴀᴘᴘʀᴏᴠᴇ ᴛʜɪs ᴀᴄᴛɪᴏɴ.")

@app.on_callback_query(filters.regex("decline_banall"))
async def decline_banall(client, callback_query: CallbackQuery):
    user_name = callback_query.from_user.first_name
    await callback_query.message.edit_text(f"</b>ʙᴀɴᴀʟʟ ᴘʀᴏᴄᴇss ʜᴀs ʙᴇᴇɴ ᴄᴀɴᴄᴇʟᴇᴅ ʙʏ</b> {user_name}.")