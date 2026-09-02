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

DUAL_TONES = [
    ((20, 20, 20), (240, 240, 240)),
    ((25, 30, 45), (250, 250, 250)),
    ((15, 40, 65), (230, 230, 230)),
    ((55, 10, 80), (255, 245, 255))
]

def trim_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    ellipsis = "…"
    try:
        if font.getlength(text) <= max_w:
            return text
        for i in range(len(text)-1, 0, -1):
            if font.getlength(text[:i] + ellipsis) <= max_w:
                return text[:i] + ellipsis
    except:
        return text[:max_w//10] + "…" if len(text) > max_w//10 else text
    return ellipsis


async def get_thumb(videoid: str, player_username: str = None) -> str:
    if player_username is None:
        player_username = app.username

    cache_path = os.path.join(CACHE_DIR, f"{videoid}_hexagon.png")
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
    except:
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
    except:
        return YOUTUBE_IMG_URL


    bg = Image.open(thumb_path).resize((1280, 720)).convert("RGB")
    bg = bg.filter(ImageFilter.GaussianBlur(30)).convert("RGBA")
    overlay = Image.new("RGBA", (1280, 720), (255, 255, 255, 40))
    bg = Image.alpha_composite(bg, overlay)

    thumb = Image.open(thumb_path).resize((520, 520)).convert("RGBA")

    hex_points = [
        (260, 0),
        (520, 130),
        (520, 390),
        (260, 520),
        (0, 390),
        (0, 130)
    ]

    mask = Image.new("L", (520, 520), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.polygon(hex_points, fill=255)

    hex_thumb = Image.new("RGBA", (520, 520), (0, 0, 0, 0))
    hex_thumb.paste(thumb, (0, 0), mask)

    border_img = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
    d = ImageDraw.Draw(border_img)
    offset = 40

    border_hex = [(x + offset, y + offset) for x, y in hex_points]

    d.polygon(border_hex, outline=(90, 0, 60, 255), width=26)

    d.polygon(border_hex, outline=(255, 100, 200, 180), width=10)

    d.polygon(border_hex, outline=(255, 40, 150, 255), width=16)

    bg.paste(border_img, (60, 60), border_img)
    bg.paste(hex_thumb, (100, 100), hex_thumb)

    draw = ImageDraw.Draw(bg)

    try:
        title_font = ImageFont.truetype("VampireMusic/assets/font.ttf", 44)
        meta_font = ImageFont.truetype("VampireMusic/assets/font.ttf", 26)
        tag_font = ImageFont.truetype("VampireMusic/assets/font2.ttf", 28)
    except:
        title_font = meta_font = tag_font = ImageFont.load_default()

    title_x = 700
    title_y = 180
    title_text = trim_to_width(title, title_font, 480)
    draw.text((title_x, title_y), title_text, fill=(0, 0, 0), font=title_font)

    meta = (
        f"YouTube | {views}\n"
        f"Duration | {duration_text}\n"
        f"Player | @{player_username}\n"
    )
    draw.multiline_text(
        (title_x, title_y + 90),
        meta,
        fill=(0, 0, 0),
        spacing=10,
        font=meta_font
    )

    bar_y = title_y + 240
    bar_w = 390

    draw.rounded_rectangle(
        (title_x, bar_y, title_x + bar_w, bar_y + 14),
        8,
        fill=(255, 255, 255, 80)
    )

    draw.rounded_rectangle(
        (title_x, bar_y, title_x + bar_w // 2, bar_y + 14),
        8,
        fill=(0, 0, 0)
    )

    try:
        os.remove(thumb_path)
    except:
        pass

    bg.save(cache_path)
    return cache_path
