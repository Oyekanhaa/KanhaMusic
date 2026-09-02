from pyrogram.enums import ParseMode
from VampireMusic import app
from VampireMusic.utils.database import is_on_off
from config import LOGGER_ID


async def play_logs(message, streamtype):
    if not await is_on_off(2):
        return

    # Safe values
    chat_id = message.chat.id
    chat_title = message.chat.title or "Private Chat"
    chat_username = f"@{message.chat.username}" if message.chat.username else "No Username"

    user_id = message.from_user.id if message.from_user else "Unknown"
    user_mention = message.from_user.mention if message.from_user else "Unknown"
    user_username = (
        f"@{message.from_user.username}"
        if message.from_user and message.from_user.username
        else "No Username"
    )

    # Safe query extraction
    query = "No Query"
    if message.text:
        parts = message.text.split(None, 1)
        if len(parts) > 1:
            query = parts[1]

    logger_text = f"""
<b>❖ {app.mention} ᴘʟᴀʏ ʟᴏɢ</b>

<b>● ᴄʜᴀᴛ ɪᴅ ➠</b> <code>{chat_id}</code>
<b>● ᴄʜᴀᴛ ɴᴀᴍᴇ ➠</b> {chat_title}
<b>● ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ ➠</b> {chat_username}

<b>● ᴜsᴇʀ ɪᴅ ➠</b> <code>{user_id}</code>
<b>● ɴᴀᴍᴇ ➠</b> {user_mention}
<b>● ᴜsᴇʀɴᴀᴍᴇ ➠</b> {user_username}

<b>● ǫᴜᴇʀʏ ➠</b> {query}
<b>● sᴛʀᴇᴀᴍᴛʏᴘᴇ ➠</b> {streamtype}
"""

    if chat_id != LOGGER_ID:
        try:
            await app.send_message(
                chat_id=LOGGER_ID,
                text=logger_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except Exception:
            pass
