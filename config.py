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
from pyrogram import filters

load_dotenv()

# ✅ Time Conversion Utility
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))

# ✅ Basic Config
API_ID = int(getenv("API_ID", ""))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "")
COOKIES = getenv("COOKIES", None)
MONGO_DB_URI = getenv("MONGO_DB_URI", "")

# ✅ Duration Config
DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 54000))
SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "54000"))

# ✅ Limits Conversion (after defining time_to_seconds)
DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))
SONG_DOWNLOAD_DURATION_LIMIT = int(time_to_seconds(f"{SONG_DOWNLOAD_DURATION}:00"))

# ✅ Owner & Bot Identity
LOGGER_ID = int(getenv("LOGGER_ID", "-100206022417"))
OWNER_ID = int(getenv("OWNER_ID", "7980630836"))
BOT_USERNAME = getenv("BOT_USERNAME", "")

# ✅ Command Handler
COMMAND_HANDLER = getenv("COMMAND_HANDLER", "! / .").split()

# ✅ Heroku
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

# ✅ Git & Upstream Repo
UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/ISTKHAR-CODER786/Syn")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", "")  # Only for private repo

# ✅ Support Links
SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/VAMPIRE_PROMOTION")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/llTEAM_VAMPIREll")

# YT-API 
API_URL = getenv("API_URL", 'https://api.nexgenbots.xyz') #youtube song url
VIDEO_API_URL = getenv("VIDEO_API_URL", 'https://api.video.nexgenbots.xyz')
API_KEY = getenv("API_KEY", "NxGBNexGenBots67b7b6") 

# ✅ Auto Features
AUTO_LEAVING_ASSISTANT = bool(getenv("AUTO_LEAVING_ASSISTANT", False))
AUTO_SUGGESTION_MODE = getenv("AUTO_SUGGESTION_MODE", "True")
AUTO_SUGGESTION_TIME = int(getenv("AUTO_SUGGESTION_TIME", "500"))

# ✅ Spotify
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "1c21247d714244ddbb09925dac565aed")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "709e1a2969664491b58200860623ef19")

# ✅ Limits
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", 25))
CLEANMODE_DELETE_MINS = int(getenv("CLEANMODE_MINS", "5"))
TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", 21474836480))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", 21474836480))

# ✅ String Sessions
STRING1 = getenv("STRING_SESSION", "")
STRING2 = getenv("STRING_SESSION2", None)
STRING3 = getenv("STRING_SESSION3", None)
STRING4 = getenv("STRING_SESSION4", None)
STRING5 = getenv("STRING_SESSION5", None)

# ✅ Runtime Storage
BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}
chatstats = {}
userstats = {}
clean = []

# ✅ UI Images
START_IMG_URL = getenv("START_IMG_URL", "https://files.catbox.moe/7tg6zk.jpg")
PING_IMG_URL = getenv("PING_IMG_URL", "https://files.catbox.moe/7tg6zk.jpg")
PLAYLIST_IMG_URL = "https://files.catbox.moe/xp3phx.jpg"
STATS_IMG_URL = "https://files.catbox.moe/7tg6zk.jpg"
TELEGRAM_AUDIO_URL = "https://files.catbox.moe/xp3phx.jpg"
TELEGRAM_VIDEO_URL = "https://files.catbox.moe/xp3phx.jpg"
STREAM_IMG_URL = "https://files.catbox.moe/xp3phx.jpg"
SOUNCLOUD_IMG_URL = "https://files.catbox.moe/xp3phx.jpg"
YOUTUBE_IMG_URL = "https://files.catbox.moe/xp3phx.jpg"
SPOTIFY_ARTIST_IMG_URL = "https://files.catbox.moe/xp3phx.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://files.catbox.moe/xp3phx.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://files.catbox.moe/xp3phx.jpg"

# ✅ URL Validation
if SUPPORT_CHANNEL and not re.match(r"(?:http|https)://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] - Your SUPPORT_CHANNEL URL is invalid. Must start with https://")

if SUPPORT_CHAT and not re.match(r"(?:http|https)://", SUPPORT_CHAT):
    raise SystemExit("[ERROR] - Your SUPPORT_CHAT URL is invalid. Must start with https://")
