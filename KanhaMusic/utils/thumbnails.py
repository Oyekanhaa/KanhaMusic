import os
import re
import math
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from py_yt import VideosSearch
from config import YOUTUBE_IMG_URL
from KanhaMusic import app

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════
#  STYLE SETTING — "sunburst" ya "hexagon" likho
# ══════════════════════════════════════════════════════════════════
THUMB_STYLE = "sunburst"   # <-- change to "hexagon" for old style
# ══════════════════════════════════════════════════════════════════

W, H = 1280, 720

# ✅ EXACT colors — pixel-scanned from original thumbnail image
BG_ORANGE    = (254, 155,  51)   # main background orange
RAY_DARK     = (255, 140,  25)   # dark ray — slightly deeper orange
CARD_WHITE   = (255, 251, 239)   # card border — warm cream/white
SHADOW_COLOR = (  2,   0,   1)   # card shadow — pure near-black

# ✅ EXACT card coordinates — pixel-scanned from original thumbnail
CARD_X, CARD_Y   = 720, 110      # card top-left
CARD_R, CARD_B   = 1200, 590     # card bottom-right  (480x480 px)
SHADOW_OFFSET    = 15            # shadow shifts 15px right + 15px down
CARD_BORDER_W    = 4             # white/cream border thickness (px)


# ─────────────────────────────────────────────────────────────────
#  HELPER: trim text to fit width
# ─────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────
#  STYLE 1 — ORANGE SUNBURST
# ─────────────────────────────────────────────────────────────────
def _sunburst_thumb(
    raw_path: str,
    title: str,
    channel: str,
    duration_text: str,
    player_username: str,
    cache_path: str,
) -> str:

    # Sunburst background
    bg   = Image.new("RGB", (W, H), BG_ORANGE)
    draw = ImageDraw.Draw(bg)
    cx, cy = W // 2, H // 2
    R = max(W, H) * 1.6

    for i in range(24):
        a0  = math.radians(i       * (360 / 24))
        a1  = math.radians((i + 1) * (360 / 24))
        pts = [
            (cx, cy),
            (cx + R * math.cos(a0), cy + R * math.sin(a0)),
            (cx + R * math.cos(a1), cy + R * math.sin(a1)),
        ]
        draw.polygon(pts, fill=RAY_DARK if i % 2 == 0 else BG_ORANGE)

    # Soft centre glow
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd  = ImageDraw.Draw(vig)
    for r in range(500, 0, -15):
        alpha = int(60 * (1 - r / 500))
        vd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*BG_ORANGE, alpha))
    bg   = Image.alpha_composite(bg.convert("RGBA"), vig).convert("RGB")
    draw = ImageDraw.Draw(bg)

    # Fonts
    try:
        f_title   = ImageFont.truetype("KanhaMusic/assets/font.ttf",  82)
        f_channel = ImageFont.truetype("KanhaMusic/assets/font.ttf",  40)
        f_meta    = ImageFont.truetype("KanhaMusic/assets/font.ttf",  34)
        f_time    = ImageFont.truetype("KanhaMusic/assets/font2.ttf", 30)
    except Exception:
        f_title = f_channel = f_meta = f_time = ImageFont.load_default()

    # Left text
    TX, TY = 60, 220
    draw.text((TX, TY),       trim_to_width(title, f_title, 580),  fill=(0,0,0), font=f_title)
    draw.text((TX, TY + 100), f"Channel: {channel}",               fill=(0,0,0), font=f_channel)
    draw.text((TX, TY + 155), f"Playing on: @{player_username}",   fill=(0,0,0), font=f_meta)

    # Progress bar
    BL, BT, BB, BR = 84, 460, 470, 582
    BRAD   = (BB - BT) // 2
    FILL_R = BL + (BR - BL) // 2
    KCX    = FILL_R
    KCY    = (BT + BB) // 2

    draw.rounded_rectangle((BL, BT, BR, BB), radius=BRAD, fill=(200, 198, 196))
    draw.rounded_rectangle((BL, BT, FILL_R, BB), radius=BRAD, fill=(0, 0, 0))
    draw.ellipse((KCX - 13, KCY - 13, KCX + 13, KCY + 13), fill=(0, 0, 0))
    draw.text((BL,       490), "0:00",        fill=(0,0,0), font=f_time)
    draw.text((BR - 65,  490), duration_text, fill=(0,0,0), font=f_time)

    # ── Card shadow (drawn first, behind card) ──
    draw.rectangle(
        (
            CARD_X + SHADOW_OFFSET,
            CARD_Y + SHADOW_OFFSET,
            CARD_R + SHADOW_OFFSET,
            CARD_B + SHADOW_OFFSET,
        ),
        fill=SHADOW_COLOR,
    )

    # ── Card white/cream border ──
    draw.rectangle((CARD_X, CARD_Y, CARD_R, CARD_B), fill=CARD_WHITE)

    # ── Album art pasted inside card with border inset ──
    try:
        art_w = (CARD_R - CARD_X) - CARD_BORDER_W * 2
        art_h = (CARD_B - CARD_Y) - CARD_BORDER_W * 2
        yt = Image.open(raw_path).convert("RGB").resize(
            (art_w, art_h), Image.LANCZOS
        )
        bg.paste(yt, (CARD_X + CARD_BORDER_W, CARD_Y + CARD_BORDER_W))
    except Exception:
        pass

    bg.save(cache_path)
    return cache_path


# ─────────────────────────────────────────────────────────────────
#  STYLE 2 — HEXAGON + PINK BORDER (original style)
# ─────────────────────────────────────────────────────────────────
def _hexagon_thumb(
    raw_path: str,
    title: str,
    duration_text: str,
    views: str,
    player_username: str,
    cache_path: str,
) -> str:

    # Blurred background
    bg = Image.open(raw_path).resize((W, H)).convert("RGB")
    bg = bg.filter(ImageFilter.GaussianBlur(30)).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (255, 255, 255, 40))
    bg = Image.alpha_composite(bg, overlay)

    # Hexagon cut
    thumb = Image.open(raw_path).resize((520, 520)).convert("RGBA")
    hex_points = [
        (260, 0), (520, 130), (520, 390),
        (260, 520), (0, 390), (0, 130)
    ]
    mask = Image.new("L", (520, 520), 0)
    ImageDraw.Draw(mask).polygon(hex_points, fill=255)
    hex_thumb = Image.new("RGBA", (520, 520), (0, 0, 0, 0))
    hex_thumb.paste(thumb, (0, 0), mask)

    # 3D Pink border
    border_img = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
    d = ImageDraw.Draw(border_img)
    border_hex = [(x + 40, y + 40) for x, y in hex_points]
    d.polygon(border_hex, outline=(90, 0, 60, 255),    width=26)
    d.polygon(border_hex, outline=(255, 100, 200, 180), width=10)
    d.polygon(border_hex, outline=(255, 40, 150, 255),  width=16)

    bg.paste(border_img, (60, 60), border_img)
    bg.paste(hex_thumb,  (100, 100), hex_thumb)

    draw = ImageDraw.Draw(bg)

    # Fonts
    try:
        f_title = ImageFont.truetype("KanhaMusic/assets/font.ttf",  44)
        f_meta  = ImageFont.truetype("KanhaMusic/assets/font.ttf",  26)
        f_tag   = ImageFont.truetype("KanhaMusic/assets/font2.ttf", 28)
    except Exception:
        f_title = f_meta = f_tag = ImageFont.load_default()

    # Title + meta
    tx, ty = 700, 180
    draw.text((tx, ty), trim_to_width(title, f_title, 480), fill=(0,0,0), font=f_title)
    meta = (
        f"YouTube | {views}\n"
        f"Duration | {duration_text}\n"
        f"Player | @{player_username}\n"
    )
    draw.multiline_text((tx, ty + 90), meta, fill=(0,0,0), spacing=10, font=f_meta)

    # Progress bar
    bar_y = ty + 240
    draw.rounded_rectangle((tx, bar_y, tx + 390, bar_y + 14), 8, fill=(255, 255, 255, 80))
    draw.rounded_rectangle((tx, bar_y, tx + 195, bar_y + 14), 8, fill=(0, 0, 0))

    # Branding
    brand = "DEV :- Kanha"
    bw    = f_tag.getlength(brand)
    draw.text((W - bw - 50, 680), brand, fill=(0,0,0), font=f_tag)

    bg_rgb = bg.convert("RGB")
    bg_rgb.save(cache_path)
    return cache_path


# ─────────────────────────────────────────────────────────────────
#  MAIN FUNCTION — called by bot
# ─────────────────────────────────────────────────────────────────
async def get_thumb(videoid: str, player_username: str = None) -> str:
    if player_username is None:
        player_username = app.username

    style      = THUMB_STYLE.lower()
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_{style}.png")
    if os.path.exists(cache_path):
        return cache_path

    # Fetch video info
    try:
        results   = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        search    = await results.next()
        data      = search.get("result", [])[0]
        title     = re.sub(r"\W+", " ", data.get("title", "Unknown Title")).title()
        thumb_url = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration  = data.get("duration")
        channel   = data.get("channel", {}).get("name", "YouTube")
        views     = data.get("viewCount", {}).get("short", "Unknown Views")
    except Exception:
        title, thumb_url, duration, channel, views = (
            "Unknown", YOUTUBE_IMG_URL, None, "YouTube", "Unknown"
        )

    is_live       = not duration or str(duration).lower() in {"live", "live now", ""}
    duration_text = "LIVE" if is_live else (duration or "Unknown")

    # Download YouTube thumbnail
    raw_path = os.path.join(CACHE_DIR, f"raw_{videoid}.jpg")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumb_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(raw_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL
    except Exception:
        return YOUTUBE_IMG_URL

    # Generate thumbnail based on selected style
    try:
        if style == "sunburst":
            result = _sunburst_thumb(
                raw_path, title, channel, duration_text, player_username, cache_path
            )
        else:   # hexagon (default fallback)
            result = _hexagon_thumb(
                raw_path, title, duration_text, views, player_username, cache_path
            )
    except Exception:
        result = YOUTUBE_IMG_URL

    # Cleanup raw download
    try:
        os.remove(raw_path)
    except Exception:
        pass

    return result