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


import asyncio
from time import time
import os
import sys
from pyrogram import Client, enums
from pyrogram import filters
from pyrogram.errors import ChatAdminRequired
from pyrogram.types import ChatPermissions, ChatPrivileges, Message
from KanhaMusic import app
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.errors import MessageDeleteForbidden, RPCError
from config import OWNER_ID

async def is_authorized(client, chat_id, user_id):
    chat_member = await client.get_chat_member(chat_id, user_id)
    return user_id == OWNER_ID or chat_member.status == enums.ChatMemberStatus.OWNER

@app.on_message(filters.command(["unbanall"], prefixes=["/", "!", "."]))
async def unbanall_command(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if await is_authorized(client, chat_id, user_id):
        # Send confirmation message with buttons
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("ᴀᴘᴘʀᴏᴠᴇ", callback_data="approve_unbanall"),
                    InlineKeyboardButton("ᴅᴇᴄʟɪɴᴇ", callback_data="decline_unbanall")
                ]
            ]
        )
        await message.reply_text(
            "ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜɴʙᴀɴ ᴀʟʟ ʙᴀɴɴᴇᴅ ᴜsᴇʀs? ᴏɴʟʏ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴄᴀɴ ᴀᴘᴘʀᴏᴠᴇ ᴛʜɪs ᴀᴄᴛɪᴏɴ.",
            reply_markup=reply_markup
        )
    else:
        await message.reply_text("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ. ᴏɴʟʏ ᴛʜᴇ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs.")

@app.on_callback_query(filters.regex("approve_unbanall|decline_unbanall"))
async def callback_handler(client, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if await is_authorized(client, chat_id, user_id):
        approver_name = callback_query.from_user.first_name  # Fetch approver's name

        if callback_query.data == "approve_unbanall":
            
            await callback_query.message.edit_text("ᴜɴʙᴀɴᴀʟʟ ꜱᴛᴀʀᴛɪɴɢ ...")

            bot = await client.get_chat_member(chat_id, client.me.id)
            bot_permission = bot.privileges.can_restrict_members

            if bot_permission:
                unban_count = 0  
                async for member in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.BANNED):
                    try:
                        await client.unban_chat_member(chat_id, member.user.id)
                        unban_count += 1  
                    except Exception:
                        pass

                await callback_query.message.edit_text(
                    f"<u><b>⬤ ᴜɴʙᴀɴ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!</u></b>\n\n<b>● ᴛᴏᴛᴀʟ ᴜsᴇʀs ➠</b> {unban_count}\n<b>● ᴜɴʙᴀɴɴᴇᴅ ʙʏ ➠</b> {approver_name}"
                )
            else:
                await callback_query.message.edit_text("ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴛʜᴇ ʀɪɢʜᴛ ᴛᴏ ᴜɴʙᴀɴ ᴜsᴇʀs ᴏʀ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ɪɴ sᴜᴅᴏ ᴜsᴇʀs.")
        elif callback_query.data == "decline_unbanall":
            
            await callback_query.message.edit_text("ᴜʙᴀɴᴀʟʟ ᴄᴏᴍᴍᴀɴᴅ ᴡᴀs ᴅᴇᴄʟɪɴᴇᴅ.")
    else:
        await callback_query.answer("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴀᴘᴘʀᴏᴠᴇ ᴏʀ ᴅᴇᴄʟɪɴᴇ ᴛʜɪs ᴀᴄᴛɪᴏɴ.", show_alert=True)