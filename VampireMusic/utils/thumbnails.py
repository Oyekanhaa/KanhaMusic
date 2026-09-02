import os
import re
import random

import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from py_yt import VideosSearch

from config import YOUTUBE_IMG_URL
from VampireMusic import app

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Exact match to the Go NEON_COLORS list
NEON_COLORS = [
    (0, 255, 255),    # cyan
    (255, 0, 255),    # magenta
    (0, 255, 128),    # green-cyan
    (255, 255, 0),    # yellow
    (255, 105, 180),  # hot pink
]

FONT_TITLE = "VampireMusic/assets/font.ttf"
FONT_META = "VampireMusic/assets/font.ttf"
FONT_TAG = "VampireMusic/assets/font2.ttf"

W, H = 1280, 720
RECT_W, RECT_H = 842, 412
RECT_X = (W - RECT_W) // 2  # 219
RECT_Y = 150


def trim_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    ellipsis = "…"
    try:
        if font.getlength(text) <= max_w:
            return text
        for i in range(len(text) - 1, 0, -1):
            if font.getlength(text[:i] + ellipsis) <= max_w:
                return text[:i] + ellipsis
    except Exception:
        return text[: max_w // 10] + "…" if len(text) > max_w // 10 else text
    return ellipsis


async def get_thumb(videoid: str, player_username: str = None) -> str:
    if player_username is None:
        player_username = app.username

    cache_path = os.path.join(CACHE_DIR, f"{videoid}_neon.png")
    if os.path.exists(cache_path):
        return cache_path

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        search = await results.next()
        data = search.get("result", [])[0]
        title = re.sub(r"\W+", " ", data.get("title", "Unknown Title")).title()
        thumbnail = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration")
        views = data.get("viewCount", {}).get("short", "Unknown Views")
    except Exception:
        title, thumbnail, duration, views = "Unknown", YOUTUBE_IMG_URL, None, "Unknown"

    is_live = not duration or str(duration).lower() in {"live", "live now", ""}
    duration_text = "Live" if is_live else duration or "Unknown"

    thumb_path = os.path.join(CACHE_DIR, f"thumb_{videoid}.png")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as r:
                if r.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await r.read())
    except Exception:
        return YOUTUBE_IMG_URL

    try:
        orig_thumb = Image.open(thumb_path).convert("RGB")
    except Exception:
        return YOUTUBE_IMG_URL

    # ── 1. Build 1280x720 blurred background ──
    base = orig_thumb.resize((W, H), Image.LANCZOS)
    blur_bg = base.filter(ImageFilter.GaussianBlur(20))
    blur_bg = ImageEnhance.Brightness(blur_bg).enhance(0.4)
    blur_bg = blur_bg.convert("RGBA")

    # ── 2. Pick a random neon color ──
    neon = random.choice(NEON_COLORS)

    # ── 3. Neon glow rectangle (flat, not rounded) ──
    glow_w, glow_h = RECT_W + 80, RECT_H + 80  # 922 x 492
    glow = Image.new("RGBA", (glow_w, glow_h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    for r in range(40, 0, -4):
        alpha = int(255 * r / 40) // 2
        glow_draw.rectangle(
            [r, r, glow_w - r, glow_h - r],
            outline=(*neon, alpha),
            width=4,
        )

    gx, gy = RECT_X - 40, RECT_Y - 40  # 179, 110
    blur_bg.paste(glow, (gx, gy), glow)

    # ── 4. Paste resized track thumbnail ──
    thumb = orig_thumb.resize((RECT_W, RECT_H), Image.LANCZOS).convert("RGBA")
    blur_bg.paste(thumb, (RECT_X, RECT_Y), thumb)

    # ── 5. Draw text ──
    draw = ImageDraw.Draw(blur_bg)

    try:
        title_font = ImageFont.truetype(FONT_TITLE, 38)
        meta_font = ImageFont.truetype(FONT_META, 22)
        tag_font = ImageFont.truetype(FONT_TAG, 26)
    except Exception:
        title_font = meta_font = tag_font = ImageFont.load_default()

    # Title — white, centered, trimmed to 800px
    title_y = RECT_Y + RECT_H + 40  # 602
    trimmed_title = trim_to_width(title, title_font, 800)
    tw = title_font.getlength(trimmed_title)
    draw.text(((W - tw) / 2, title_y), trimmed_title, fill=(255, 255, 255), font=title_font)

    # Meta line — neon colored, centered
    meta_y = title_y + 50  # 652
    meta_text = f"YouTube:{views} |Time:{duration_text} |Player:@{player_username}"
    mw = meta_font.getlength(meta_text)
    draw.text(((W - mw) / 2, meta_y), meta_text, fill=(*neon, 255), font=meta_font)

    # Corner tags
    padding = 25

    dev_text = "Dev :-  @xoknha"
    dw = tag_font.getlength(dev_text)
    draw.text((W - dw - padding, padding), dev_text, fill=(*neon, 255), font=tag_font)

    draw.text((padding, H - 60), "KanhaMusic", fill=(*neon, 255), font=tag_font)

    # ── 6. Save ──
    final = blur_bg.convert("RGB")

    try:
        os.remove(thumb_path)
    except Exception:
        pass

    final.save(cache_path)
    return cache_path
