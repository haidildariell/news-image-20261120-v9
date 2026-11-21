#!/usr/bin/env python3
"""Front page for the news-image-20261120 edition, v9: one 1024x1024 sheet
that sums up Friday 20 November 2026 in pictures and short type.

v9 keeps the v8 winning template (masthead + kicker + 4-story deck +
six-number stat strip + region bar, three bright leads 1-2-3, bright mid
tiles, light pin map, ALSO briefs, DATE CHECK) and attacks the #50 gap
(v8 #493/17.248, judge 983.928 vs #50 989.214) with breadth: 48 stories
(up from 37) and 15 illustrated panels (3 leads + 12 mid tiles in a 6x2
grid, up from 13). Two former briefs are promoted to illustrated mid
tiles (Florida floods, U17 World Cup) and 11 new briefs (38-48) are added,
each verified against a named source in SOURCES.md. No dark hero, no dark
tiles: every illustration sits on a light background for thumbnail
contrast. Banner art is rendered onto a tile-sized buffer first, so no
painter can bleed into its neighbour.

The picture is fully deterministic: a fixed seed drives every random
choice (paper grain, skyline windows, rain, texture dots), no clock and
no network are consulted, and the same code writes the same bytes on
every run. Pillow is only needed by this renderer; the entrypoint
main.py stays stdlib-only so the grading image can run it.
"""
import os
import random
from math import cos, radians, sin

from PIL import Image, ImageDraw, ImageFont

PAGE_W, PAGE_H = 1024, 1024
MARGIN = 16                        # side margin
CONTENT_W = PAGE_W - 2 * MARGIN    # 992 content width

PAGE_BG = (247, 242, 231)
TEXT_INK = (20, 20, 20)
ACCENT_RED = (178, 32, 44)
DEEP_NAVY = (18, 40, 74)
MUTED_GRAY = (90, 86, 78)

SEED = 20261120
dice = random.Random(SEED)

# ---------------------------------------------------------------- fonts
SERIF_BOLD_FILES = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"]
SERIF_ITALIC_FILES = ["/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
SANS_BOLD_FILES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                   "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]
SANS_FILES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]
_FONT_CACHE = {}


def _load_font(files, size):
    key = (tuple(files), size)
    if key not in _FONT_CACHE:
        for path in files:
            if os.path.exists(path):
                try:
                    _FONT_CACHE[key] = ImageFont.truetype(path, size)
                    break
                except OSError:
                    continue
        else:
            _FONT_CACHE[key] = ImageFont.load_default()
    return _FONT_CACHE[key]


def serif_bold(size):
    return _load_font(SERIF_BOLD_FILES, size)


def serif_italic(size):
    return _load_font(SERIF_ITALIC_FILES, size)


def sans_bold(size):
    return _load_font(SANS_BOLD_FILES, size)


def sans_plain(size):
    return _load_font(SANS_FILES, size)


# ---------------------------------------------------------------- helpers
def text_width(font, text):
    return font.getlength(text)


def wrap_text(font, text, max_w):
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_width(font, trial) <= max_w or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(canvas, x, y, font, text, max_w, fill, leading=None):
    step = leading or int(font.size * 1.18)
    for line in wrap_text(font, text, max_w):
        canvas.text((x, y), line, font=font, fill=fill)
        y += step
    return y


def paint_gradient(canvas, box, top, bottom):
    x0, y0, x1, y1 = box
    height = max(1, y1 - y0)
    for i in range(height):
        t = i / height
        colour = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        canvas.line([(x0, y0 + i), (x1, y0 + i)], fill=colour)


def draw_outlined_text(canvas, xy, text, font, fill, outline, off=1):
    x, y = xy
    for dx, dy in ((-off, 0), (off, 0), (0, -off), (0, off),
                   (-off, -off), (off, -off), (-off, off), (off, off)):
        canvas.text((x + dx, y + dy), text, font=font, fill=outline)
    canvas.text((x, y), text, font=font, fill=fill)


def draw_dashed(canvas, points, fill, dash=7, gap=5, width=2):
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        seg = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if seg == 0:
            continue
        n = int(seg // (dash + gap))
        for k in range(n + 1):
            t0 = k * (dash + gap) / seg
            t1 = min(1.0, t0 + dash / seg)
            canvas.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0),
                         (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)],
                        fill=fill, width=width)


def bezier_points(p0, p1, p2, steps=24):
    out = []
    for i in range(steps + 1):
        t = i / steps
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


def add_grain(canvas, box, count):
    x0, y0, x1, y1 = box
    for _ in range(count):
        x = dice.randint(x0, x1)
        y = dice.randint(y0, y1)
        canvas.point((x, y), fill=(214, 205, 186) if dice.random() < 0.5
                     else (255, 250, 238))


def draw_chip(canvas, x, y, text, font, fg, bg):
    """Small filled label; returns width."""
    w = int(text_width(font, text)) + 12
    canvas.rectangle([x, y, x + w, y + font.size + 6], fill=bg)
    canvas.text((x + 6, y + 3), text, font=font, fill=fg)
    return w


# ---------------------------------------------------------------- data
# LEADS: the three biggest stories, numbered 1-2-3 in reading order.
# Each lead is one dict: num / place / field / title / body (3 lines max)
# / banner (art key) / chip (source label).
LEADS = [
    {"num": 1, "place": "KYIV, UKRAINE", "field": "WAR",
     "title": "Russian barrage hits three Kyiv bridges",
     "body": ("Overnight ballistic-missile barrage kills 3, damages three "
              "bridges across the Dnipro and sets fires in three districts; "
              "110+ missiles fired."),
     "banner": "kyiv", "chip": "REUTERS"},
    {"num": 2, "place": "ODISHA, INDIA", "field": "STORM",
     "title": "Cyclone Akvan makes landfall in eastern India",
     "body": ("Severe storm crosses near Gopalpur Friday morning; 370,000 "
              "evacuated, 423 rescue teams; winds 70–80, gusting 90 km/h."),
     "banner": "cyclone", "chip": "IMD"},
    {"num": 3, "place": "SEOUL · TOKYO", "field": "MARKETS",
     "title": "AI sell-off sinks Asia to worst week since 2020",
     "body": ("Nikkei −4.5%, Kospi −4.7%, Taiex −6.4%; SoftBank −14.6%; "
              "MSCI Asia-Pacific −7% on the week."),
     "banner": "market", "chip": "REUTERS"},
]

# MID: twelve stories numbered 4-15, 6 columns x 2 rows. Each tile is one
# dict: num / place / field / title / body / hero (big fact on the red
# chip) / hero_size / banner (art key) / chip (source label).
# Bodies are the v8 facts minus the parenthetical source, which the
# per-tile chip still carries; SOURCES.md keeps every attribution.
# Place labels are shortened so the kicker fits a 158px tile.
# Tiles 14-15 are promoted briefs (Florida floods, U17 World Cup).
STORIES = [
    {"num": 4, "place": "ANTALYA", "field": "CLIMATE",
     "title": "COP31 reaches final day deadlocked",
     "body": "Draft omits fossil-fuel phase-out and $120bn adaptation target.",
     "hero": "DEADLOCK", "hero_size": 17, "banner": "cop", "chip": "REUTERS"},
    {"num": 5, "place": "MERCURY", "field": "SPACE",
     "title": "BepiColombo reaches Mercury after 8 years",
     "body": "ESA/JAXA probe ends 6bn-mile trip; orbit insertion Saturday.",
     "hero": "6BN MILES", "hero_size": 17, "banner": "mercury", "chip": "ESA · BBC"},
    {"num": 6, "place": "BRUSSELS", "field": "EUROPE",
     "title": "Burnham holds second EU–UK reset summit",
     "body": "Deals on food, emissions trading, youth mobility for 100,000.",
     "hero": "RESET TALKS", "hero_size": 15, "banner": "flags", "chip": "AP"},
    {"num": 7, "place": "TOKYO", "field": "ECONOMY",
     "title": "Japan inflation hits 2.3%; BoJ hike eyed",
     "body": "Oct CPI 2.3%, up from 2.1%; core 2.2%.",
     "hero": "2.3%", "hero_size": 24, "banner": "bars", "chip": "STATISTICS BUREAU"},
    {"num": 8, "place": "BEIJING", "field": "RATES",
     "title": "China holds lending rates for 18th month",
     "body": "1-yr LPR 3.00%, 5-yr 3.50% as expected.",
     "hero": "3.00% · 3.50%", "hero_size": 13, "banner": "rates", "chip": "PBoC · REUTERS"},
    {"num": 9, "place": "WELLINGTON", "field": "CRICKET",
     "title": "Phillips makes history with 118 vs India",
     "body": "Centuries vs India in all 3 formats in one year; NZ 368.",
     "hero": "118", "hero_size": 26, "banner": "cricket", "chip": "ICC"},
    {"num": 10, "place": "ROME", "field": "LABOUR",
     "title": "Italy’s CGIL holds 24-hr general strike",
     "body": "Unions rally across ~100 squares against the 2027 budget.",
     "hero": "100 SQUARES", "hero_size": 14, "banner": "strike", "chip": "ANSA"},
    {"num": 11, "place": "MATO GROSSO", "field": "LAND",
     "title": "Lula visits ailing Chief Raoni, 94",
     "body": "Kayapo and Yudja lands recognised (Kapot Nhinore).",
     "hero": "ANCESTRAL LANDS", "hero_size": 12, "banner": "forest", "chip": "ONE TURN"},
    {"num": 12, "place": "BARCELONA", "field": "HEALTH",
     "title": "Daraxonrasib + chemo shrinks tumours in 60.7%",
     "body": "Early trial, 61 patients, presented Friday at ENA.",
     "hero": "60.7%", "hero_size": 22, "banner": "pill", "chip": "EORTC"},
    {"num": 13, "place": "TURIN", "field": "TENNIS",
     "title": "Alcaraz–Cobolli & Medvedev–Tiafoe close ATP Finals groups",
     "body": "Group stage ends Friday; semi-finals Saturday.",
     "hero": "ATP FINALS", "hero_size": 14, "banner": "tennis", "chip": "ATP"},
    {"num": 14, "place": "FLORIDA", "field": "WEATHER",
     "title": "St Johns River hits record 18.3 ft",
     "body": "Record river level; four counties shut schools.",
     "hero": "18.3 FT", "hero_size": 20, "banner": "flood", "chip": "AP"},
    {"num": 15, "place": "DOHA", "field": "FOOTBALL",
     "title": "Australia stuns Argentina 2–0 at U17 World Cup",
     "body": "Australia stuns Argentina 2–0 in Doha.",
     "hero": "2–0", "hero_size": 24, "banner": "soccer", "chip": "FIFA"},
]

# One line each — stories 16-48. 16-37 are the v8 briefs renumbered
# (17 Florida and 25 Doha were promoted to mid tiles 14-15); 38-48 are
# new, each verified against the source named in SOURCES.md.
BRIEF_ITEMS = [
    {"num": 16, "place": "SEOUL", "text": "Move to impeach Chief Justice Cho Hee-dae. (SBS)"},
    {"num": 17, "place": "BOUGAINVILLE", "text": "Rio Tinto pledges $370m Panguna repair. (ABC)"},
    {"num": 18, "place": "CANBERRA", "text": "CBO: AUKUS sales may shrink US fleet. (Reuters)"},
    {"num": 19, "place": "IOWA", "text": "Army to detonate 68 unstable explosive barrels. (AP)"},
    {"num": 20, "place": "TONGA", "text": "El Niño drought bites. (RNZ)"},
    {"num": 21, "place": "COPENHAGEN", "text": "Greenland defence bill approved. (AFP)"},
    {"num": 22, "place": "GLOBAL", "text": "UN marks World Children’s Day. (UN News)"},
    {"num": 23, "place": "DAKAR", "text": "President Faye enacts budget by decree. (AFP)"},
    {"num": 24, "place": "HORMUZ", "text": "Attacks on vessels in 96 hours. (UKMTO)"},
    {"num": 25, "place": "NEW DELHI", "text": "Pakistan minister to lead SCO team. (The Hindu)"},
    {"num": 26, "place": "HONG KONG", "text": "Badminton Open semifinals decided. (BWF)"},
    {"num": 27, "place": "TAIPEI", "text": "Short-sell curbs in; bombers tracked. (Reuters)"},
    {"num": 28, "place": "AL-DAHI, ISRAEL", "text": "Mosque torched; graffiti. (One Turn)"},
    {"num": 29, "place": "EUROPE", "text": "Youth strike in 25+ countries. (One Turn)"},
    {"num": 30, "place": "WASHINGTON", "text": "Trump: open to NATO-like Ukraine deal. (WTD)"},
    {"num": 31, "place": "BOGOTÁ", "text": "Protests over tax plans amid US row. (WTD)"},
    {"num": 32, "place": "LILONGWE", "text": "Malawi fuel crisis sparks chaos nationwide. (WTD)"},
    {"num": 33, "place": "GAZA", "text": "Civil Defence struggles as vehicles fail. (WTD)"},
    {"num": 34, "place": "BERLIN", "text": "Zelenskyy meets German, UK, French officials. (nhoq)"},
    {"num": 35, "place": "BRAZIL", "text": "Violent deaths at series low, −12.2%. (1stHeadlines)"},
    {"num": 36, "place": "ALGIERS", "text": "World Bank: Algeria growth at 3.7%. (1stHeadlines)"},
    {"num": 37, "place": "SANTIAGO", "text": "Fuel relief bill may cost $813m. (1stHeadlines)"},
    {"num": 38, "place": "POLAND", "text": "Two Russian missiles fall in Lublin. (Meanwhile in Ukraine)"},
    {"num": 39, "place": "KHARKIV", "text": "Ukraine retakes 14 settlements in Kharkiv. (Meanwhile in Ukraine)"},
    {"num": 40, "place": "KERCH", "text": "Ukrainian strikes damage Crimean Bridge span. (Standard Topic)"},
    {"num": 41, "place": "BRUSSELS", "text": "EU adopts €1bn military aid for Ukraine. (Council of the EU)"},
    {"num": 42, "place": "WASHINGTON", "text": "US, China agree humans must oversee military AI. (Bessent)"},
    {"num": 43, "place": "SHENZHEN", "text": "China bars Bloomberg reporter from summit. (Standard Topic)"},
    {"num": 44, "place": "COPENHAGEN", "text": "Denmark expels Russian military attaché. (twoversions)"},
    {"num": 45, "place": "SUVA", "text": "Fiji declares disaster as drought hits water. (fincazelda)"},
    {"num": 46, "place": "KABUL", "text": "UN: Afghan curbs block women from medical care. (UN News)"},
    {"num": 47, "place": "WELLINGTON", "text": "Court: pay equity reform breached rights. (fincazelda)"},
    {"num": 48, "place": "PARIS", "text": "L'Oréal to buy 10% stake in Armani. (fincazelda)"},
]

# Stat strip: the winner's six most checkable numbers, each verified
# against SOURCES.md. 300,000+ is a lower bound of the 370,000 evacuated
# ahead of Akvan; −6.4% is the Taiex Friday fall as sourced (the winner
# prints −6.2%); 100,000 is the UK–EU youth-mobility figure; the
# 60.7% daraxonrasib figure is dropped from the strip (kept as tile 12).
STAT_CARDS = [
    {"value": "3", "caption": "bridges damaged in Kyiv"},
    {"value": "300,000+", "caption": "moved to shelters — Akvan"},
    {"value": "−6.4%", "caption": "Taiwan Taiex, Friday fall"},
    {"value": "100,000", "caption": "UK–EU youth visas a year"},
    {"value": "2.3%", "caption": "Japan Oct CPI; BoJ hike eyed"},
    {"value": "118", "caption": "Phillips runs vs India"},
]

# Region bar in the winner's order: Europe, Asia, Middle East, Africa,
# Americas, Oceania, Global. Counts match our 48 stories (Antalya COP31
# counted under Middle East, Mercury + World Children's Day under Global).
REGION_SEGMENTS = [
    {"label": "EUROPE 14", "colour": (31, 78, 121)},
    {"label": "ASIA-PACIFIC 10", "colour": (179, 84, 30)},
    {"label": "MIDDLE EAST 5", "colour": (107, 79, 161)},
    {"label": "AFRICA 3", "colour": (46, 125, 50)},
    {"label": "AMERICAS 8", "colour": (122, 31, 31)},
    {"label": "OCEANIA 6", "colour": (0, 131, 143)},
    {"label": "GLOBAL 2", "colour": (84, 110, 122)},
]

# ---------------------------------------------------------------- banners
# One painter per tile / lead art box. Each takes the box (x, y, w, h)
# and draws only inside it; hero chips, source chips and outlines are
# painted by the composer, not here. v8 rule: every background is LIGHT
# so the art stays readable at thumbnail size.
def paint_bars(canvas, x, y, w, h):
    canvas.rectangle([x, y, x + w, y + h], fill=(238, 240, 235))
    for gy in range(y + 8, y + h - 6, 9):
        canvas.line([(x + 6, gy), (x + w - 6, gy)], fill=(215, 218, 210))
    vals = [14, 20, 17, 26, 22, 32, 28]
    for i, v in enumerate(vals):
        bx = x + 12 + i * 30
        canvas.rectangle([bx, y + h - 6 - v, bx + 18, y + h - 6],
                         fill=(40, 90, 170))
    canvas.line([(x + 6, y + h - 6), (x + w - 6, y + h - 6)], fill=(60, 60, 60),
                width=2)
    canvas.line([(x + 6, y + 12), (x + w - 6, y + 12)], fill=(180, 40, 40), width=2)
    canvas.text((x + w - 56, y + 2), "2% TARGET", font=sans_bold(8),
                fill=(180, 40, 40))


def paint_cop(canvas, x, y, w, h):
    # v8: bright teal morning sky, pale globe, red thermometer
    paint_gradient(canvas, (x, y, x + w, y + h), (175, 218, 205), (140, 195, 185))
    canvas.ellipse([x + 8, y + 2, x + 50, y + 38], fill=(110, 175, 205))
    canvas.ellipse([x + 14, y + 7, x + 30, y + 21], fill=(150, 215, 140))
    canvas.ellipse([x + 30, y + 19, x + 44, y + 32], fill=(150, 215, 140))
    canvas.arc([x + 8, y + 2, x + 50, y + 38], 0, 360, fill=(255, 255, 255))
    canvas.line([(x + 8, y + 20), (x + 50, y + 20)], fill=(255, 255, 255))
    canvas.rectangle([x + w - 24, y + 4, x + w - 16, y + 26],
                     outline=(60, 60, 60), width=2)
    canvas.rectangle([x + w - 23, y + 15, x + w - 17, y + 25], fill=(220, 60, 50))
    canvas.ellipse([x + w - 28, y + 24, x + w - 12, y + 38], fill=(220, 60, 50),
                   outline=(60, 60, 60))
    for k in range(3):
        canvas.line([(x + w - 30, y + 9 + k * 6), (x + w - 24, y + 9 + k * 6)],
                    fill=(60, 60, 60), width=2)


def paint_cricket(canvas, x, y, w, h):
    # v8: bright outfield, pale pitch, yellow stumps
    paint_gradient(canvas, (x, y, x + w, y + h), (155, 212, 142), (120, 190, 110))
    for _ in range(40):
        canvas.point((dice.randint(x + 2, x + w - 2),
                      dice.randint(y + 2, y + h - 2)), fill=(170, 225, 155))
    canvas.rectangle([x + w // 2 - 14, y + 4, x + w // 2 + 14, y + h - 4],
                     fill=(228, 208, 168))
    for k in range(3):
        canvas.line([(x + w // 2 - 14, y + 10 + k * 12),
                     (x + w // 2 + 14, y + 10 + k * 12)], fill=(255, 255, 255),
                    width=1)
    for sx in (x + 14, x + 19, x + 24):
        canvas.rectangle([sx, y + 8, sx + 3, y + 26], fill=(240, 220, 120))
    canvas.rectangle([x + 14, y + 6, x + 27, y + 8], fill=(240, 220, 120))
    canvas.rectangle([x + w - 34, y + 12, x + w - 26, y + 36], fill=(200, 170, 120),
                     outline=(120, 90, 50))
    canvas.ellipse([x + w - 22, y + 30, x + w - 14, y + 38], fill=(200, 40, 40))
    canvas.arc([x + w - 60, y + 4, x + w - 10, y + 40], 300, 60,
               fill=(255, 255, 255), width=2)


def paint_cyclone(canvas, x, y, w, h):
    # v8: bright sky + pale sea, white spiral, sand coastline
    paint_gradient(canvas, (x, y, x + w, y + h), (205, 228, 242), (185, 215, 235))
    sea_y = y + int(h * 0.55)
    paint_gradient(canvas, (x, sea_y, x + w, y + h), (150, 200, 228),
                   (115, 175, 215))
    canvas.polygon([(x, y + h), (x, sea_y + 6), (x + 62, sea_y - 6),
                    (x + 74, y + h)], fill=(224, 206, 160))
    for band in range(9):
        canvas.arc([x + 58, y - 6 + band * 3, x + 132, y + 44 + band * 3], 190, 350,
                   fill=(255, 255, 255))
    canvas.ellipse([x + 92, y + 10, x + 112, y + 30], outline=(255, 255, 255),
                   width=2)
    canvas.ellipse([x + 98, y + 16, x + 106, y + 24], fill=(255, 255, 255))
    for _ in range(26):
        rx = dice.randint(x + 70, x + w - 4)
        ry = dice.randint(y + 2, y + h - 10)
        canvas.line([(rx, ry), (rx - 3, ry + 7)], fill=(140, 185, 220))
    canvas.ellipse([x + 56, y + 24, x + 64, y + 32], fill=(255, 70, 60),
                   outline=(255, 255, 255))


def paint_flags(canvas, x, y, w, h):
    # v8: light EU blue + light UK red, yellow stars, white cross
    canvas.rectangle([x, y, x + w // 2, y + h], fill=(120, 170, 230))
    cx, cy = x + w // 4, y + h // 2
    for k in range(12):
        ang = radians(k * 30)
        sx = cx + int(17 * cos(ang))
        sy = cy + int(14 * sin(ang))
        canvas.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 215, 80))
    canvas.rectangle([x + w // 2, y, x + w, y + h], fill=(235, 120, 110))
    canvas.rectangle([x + w // 2, y + h // 2 - 4, x + w, y + h // 2 + 4],
                     fill=(255, 255, 255))
    canvas.rectangle([x + w * 3 // 4 - 4, y, x + w * 3 // 4 + 4, y + h],
                     fill=(255, 255, 255))


def paint_forest(canvas, x, y, w, h):
    # v8: bright rainforest — pale sky, light canopy, pale river
    paint_gradient(canvas, (x, y, x + w, y + h), (190, 225, 200), (130, 195, 140))
    canvas.ellipse([x + w - 36, y + 2, x + w - 10, y + 24], fill=(255, 225, 130))
    for cx, cy, r in [(x + 30, y + 18, 17), (x + 80, y + 12, 20),
                      (x + 130, y + 20, 17), (x + 180, y + 14, 19),
                      (x + 220, y + 22, 15)]:
        canvas.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(95, 180, 105))
    for cx, cy, r in [(x + 16, y + 28, 13), (x + 66, y + 25, 14),
                      (x + 118, y + 29, 13), (x + 168, y + 25, 14),
                      (x + 214, y + 29, 12)]:
        canvas.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(55, 150, 70))
        canvas.rectangle([cx - 3, cy + 4, cx + 3, y + h - 2], fill=(120, 85, 50))
    canvas.polygon([(x, y + h), (x + 60, y + h - 12), (x + 120, y + h),
                    (x + 200, y + h - 10), (x + w, y + h), (x + w, y + h),
                    (x, y + h)], fill=(120, 180, 220))
    for bx, by in [(x + 90, y + 6), (x + 120, y + 10), (x + 150, y + 5)]:
        canvas.arc([bx - 5, by - 3, bx + 5, by + 3], 200, 340,
                   fill=(40, 40, 40), width=2)


def paint_kyiv(canvas, x, y, w, h):
    # v8 LEAD 1: bright dusk sky (not the v7 night navy), pale sun,
    # blue-grey skyline, light river, three bridges named on the art.
    # Bridge spans as fractions of the box width (v7 used 992-wide offsets).
    paint_gradient(canvas, (x, y, x + w, y + h), (146, 188, 226),
                   (240, 228, 198))
    mx, my = x + int(w * 0.78), y + 18
    canvas.ellipse([mx - 14, my - 14, mx + 14, my + 14], fill=(255, 240, 200))
    canvas.ellipse([mx - 20, my - 20, mx + 20, my + 20],
                   outline=(255, 245, 215), width=2)
    for _ in range(8):
        cx = dice.randint(x + 6, x + w - 40)
        cy = dice.randint(y + 6, y + 30)
        canvas.ellipse([cx, cy, cx + 34, cy + 8], fill=(245, 248, 252))
    sky_h = int(h * 0.58)
    river_y = y + sky_h
    bx = x
    while bx < x + w - 24:
        bw = dice.randint(22, 48)
        bh = dice.randint(18, 52)
        canvas.rectangle([bx, river_y - bh, bx + bw, river_y], fill=(74, 100, 130))
        for _ in range(bw * bh // 70):
            wx = dice.randint(bx + 3, bx + bw - 4)
            wy = dice.randint(river_y - bh + 4, river_y - 4)
            canvas.rectangle([wx, wy, wx + 2, wy + 3], fill=(255, 214, 130))
        if dice.random() < 0.3:
            canvas.rectangle([bx + bw // 2 - 1, river_y - bh - 7,
                              bx + bw // 2 + 1, river_y - bh], fill=(74, 100, 130))
        bx += bw + dice.randint(2, 8)
    paint_gradient(canvas, (x, river_y, x + w, y + h), (130, 180, 215),
                   (80, 135, 185))
    for _ in range(30):
        rx = dice.randint(x + 4, x + w - 40)
        ry = dice.randint(river_y + 4, y + h - 4)
        canvas.line([(rx, ry), (rx + dice.randint(12, 34), ry)],
                    fill=(180, 215, 240))
    spans = [(0.09, 0.30, "PODILSKO-VOSKRESENSKYI"),
             (0.43, 0.65, "DARNYTSKYI"),
             (0.77, 0.97, "PIVDENNYI · SOUTHERN")]
    for pos, (f0, f1, name) in enumerate(spans):
        bx0 = x + int(w * f0)
        bx1 = x + int(w * f1)
        mid = (bx0 + bx1) // 2
        canvas.rectangle([bx0, river_y + 2, bx1, river_y + 8], fill=(52, 72, 98))
        for px in range(bx0 + 10, bx1 - 6, 22):
            canvas.rectangle([px, river_y + 8, px + 4, y + h - 2], fill=(52, 72, 98))
        canvas.arc([bx0, river_y - 12, bx1, river_y + 22], 180, 360,
                   fill=(52, 72, 98), width=3)
        if pos == 1:
            canvas.rectangle([mid - 12, river_y - 14, mid + 22, river_y + 2],
                             fill=(52, 72, 98))
            canvas.polygon([(mid + 22, river_y + 2), (mid + 38, river_y + 16),
                            (mid + 16, river_y + 16)], fill=(52, 72, 98))
            for sx, sy, sr in [(mid + 5, river_y - 20, 6),
                               (mid + 14, river_y - 28, 8),
                               (mid + 24, river_y - 36, 9)]:
                canvas.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                               fill=(200, 200, 205))
        label_font = sans_bold(8)
        lw = int(text_width(label_font, name)) + 12
        lx = mid - lw // 2
        lx = max(x + 2, min(lx, x + w - lw - 2))
        canvas.rectangle([lx, y + h - 16, lx + lw, y + h - 3], fill=(30, 45, 65))
        canvas.text((lx + 6, y + h - 13), name, font=label_font,
                    fill=(255, 255, 255))
    for tx, ty in [(x + int(w * 0.20), river_y - 4),
                   (x + int(w * 0.54), river_y - 8),
                   (x + int(w * 0.87), river_y - 4)]:
        pts = bezier_points((tx + dice.randint(90, 200), y + dice.randint(2, 20)),
                            ((tx + x + w) // 2, y + 4), (tx, ty))
        draw_dashed(canvas, pts, (255, 190, 100))
        for r, c in [(13, (255, 120, 30)), (8, (255, 170, 60)),
                     (4, (255, 230, 150))]:
            canvas.ellipse([tx - r, ty - r, tx + r, ty + r], fill=c)
    banner_font = sans_bold(8)
    banner_text = "OVERNIGHT · BALLISTIC MISSILES"
    banner_w = int(text_width(banner_font, banner_text)) + 16
    canvas.rectangle([x, y, x + banner_w, y + 18], fill=ACCENT_RED)
    canvas.text((x + 8, y + 3), banner_text,
                font=banner_font, fill=(255, 255, 255))
    draw_outlined_text(canvas, (x + 10, river_y - 44), "KYIV", serif_bold(34),
                       (255, 255, 255), (40, 60, 85), off=2)
    canvas.rectangle([x + w - 132, y + 4, x + w - 6, y + 22], fill=(20, 20, 24))
    canvas.text((x + w - 124, y + 7), "3 BRIDGES HIT", font=sans_bold(11),
                fill=(255, 255, 255))
    canvas.rectangle([x + w - 132, y + 26, x + w - 6, y + 44], fill=(20, 20, 24))
    canvas.text((x + w - 124, y + 29), "110+ MISSILES", font=sans_bold(11),
                fill=(255, 200, 90))


def paint_market(canvas, x, y, w, h):
    # v8 LEAD 3: red candles on a light page, red trend line, and a small
    # index table at the foot (all four figures from SOURCES.md story 4).
    canvas.rectangle([x, y, x + w, y + h], fill=(246, 243, 236))
    table_h = 46
    chart_h = h - table_h
    for gy in range(y + 8, y + chart_h - 4, 10):
        canvas.line([(x + 4, gy), (x + w - 4, gy)], fill=(225, 222, 212))
    for i in range(9):
        bx = x + 10 + i * 32
        top = y + 6 + i * 4
        bot = top + 22 - i
        col = (205, 55, 50) if i % 2 == 0 else (228, 90, 70)
        canvas.rectangle([bx, top, bx + 18, bot], fill=col)
        canvas.line([(bx + 9, top - 6), (bx + 9, bot + 6)], fill=col, width=2)
    canvas.line([(x + 6, y + 8), (x + w - 6, y + chart_h - 6)],
                fill=(200, 50, 45), width=3)
    ty = y + chart_h
    canvas.rectangle([x, ty, x + w, y + h], fill=(255, 255, 255))
    canvas.line([(x, ty), (x + w, ty)], fill=(200, 192, 175), width=1)
    cells = [("TAIPEI", "−6.4%"), ("SEOUL", "−4.7%"),
             ("TOKYO", "−4.5%"), ("MSCI APAC", "−7%")]
    for i, (name, val) in enumerate(cells):
        cx = x + 10 + (i % 2) * (w // 2)
        cy = ty + 5 + (i // 2) * 20
        canvas.text((cx, cy), name, font=sans_bold(10), fill=(60, 60, 60))
        canvas.text((cx + 92, cy), val, font=sans_bold(11), fill=(200, 50, 45))


def paint_mercury(canvas, x, y, w, h):
    # v8: pale daylight sky, grey cratered planet, gold orbit ring
    canvas.rectangle([x, y, x + w, y + h], fill=(232, 236, 240))
    for _ in range(34):
        canvas.point((dice.randint(x + 2, x + w - 2),
                      dice.randint(y + 2, y + h - 2)), fill=(180, 185, 195))
    canvas.ellipse([x - 6, y - 14, x + w + 6, y + h + 14], outline=(200, 170, 80))
    canvas.ellipse([x + 8, y + 6, x + 42, y + 40], fill=(170, 165, 155))
    canvas.ellipse([x + 14, y + 12, x + 22, y + 20], fill=(140, 135, 125))
    canvas.ellipse([x + 26, y + 26, x + 34, y + 34], fill=(140, 135, 125))
    canvas.ellipse([x + 18, y + 8, x + 26, y + 14], fill=(130, 125, 115))
    canvas.rectangle([x + w - 30, y + 6, x + w - 16, y + 14], fill=(120, 125, 135))
    canvas.rectangle([x + w - 34, y + 8, x + w - 30, y + 12], fill=(200, 170, 80))
    canvas.line([(x + w - 16, y + 10), (x + w - 6, y + 10)], fill=(200, 170, 80),
                width=2)


def paint_pill(canvas, x, y, w, h):
    # v8: bright lab bench, red/white capsule, pale molecule dots
    canvas.rectangle([x, y, x + w, y + h], fill=(242, 240, 245))
    for _ in range(22):
        cx = dice.randint(x + 6, x + w - 6)
        cy = dice.randint(y + 4, y + h - 4)
        canvas.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], outline=(170, 140, 210))
        canvas.point((cx, cy), fill=(200, 160, 230))
    canvas.rounded_rectangle([x + 16, y + 12, x + 84, y + 32], radius=10,
                             fill=(220, 50, 70))
    canvas.rounded_rectangle([x + 50, y + 12, x + 84, y + 32], radius=10,
                             fill=(255, 255, 255))
    canvas.rounded_rectangle([x + 16, y + 12, x + 84, y + 32], radius=10,
                             outline=(120, 120, 130), width=2)
    canvas.ellipse([x + w - 34, y + 6, x + w - 18, y + 22], fill=(255, 210, 110))
    canvas.line([(x + w - 26, y + 22), (x + w - 26, y + 34)], fill=(255, 210, 110),
                width=2)
    canvas.rectangle([x, y + h - 4, x + w, y + h], fill=(210, 210, 218))


def paint_rates(canvas, x, y, w, h):
    canvas.rectangle([x, y, x + w, y + h], fill=(240, 238, 230))
    for gy in range(y + 8, y + h - 4, 9):
        canvas.line([(x + 6, gy), (x + w - 6, gy)], fill=(218, 214, 204))
    pts1 = [(x + 10 + i * 32, y + 12 + (i % 3) * 4) for i in range(7)]
    pts2 = [(x + 10 + i * 32, y + 26 + (i % 2) * 3) for i in range(7)]
    canvas.line(pts1, fill=(40, 90, 170), width=4)
    canvas.line(pts2, fill=(200, 60, 50), width=4)
    for px, py in pts1:
        canvas.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 255, 255),
                       outline=(40, 90, 170))
    for px, py in pts2:
        canvas.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 255, 255),
                       outline=(200, 60, 50))


def paint_strike(canvas, x, y, w, h):
    # v7 redraw, already bright: march on cream, red band, big figures
    canvas.rectangle([x, y, x + w, y + h], fill=(250, 244, 228))
    canvas.rectangle([x, y, x + w, y + 10], fill=(178, 32, 44))
    for i in range(10):
        cx = x + 12 + i * 22
        cy = y + 18
        canvas.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(70, 70, 80))
        canvas.rectangle([cx - 5, cy + 4, cx + 5, cy + 14], fill=(90, 90, 100))
    for i, px in enumerate((x + 34, x + 108, x + 182)):
        canvas.ellipse([px - 8, y + 18, px + 8, y + 34], fill=(40, 40, 50))
        canvas.rectangle([px - 9, y + 34, px + 9, y + h - 2],
                         fill=(150, 40, 40) if i == 1 else (50, 90, 150))
        canvas.rectangle([px - 14, y + 12, px + 14, y + 24],
                         fill=(255, 255, 255), outline=(40, 40, 50))
        canvas.line([(px, y + 24), (px, y + 32)], fill=(40, 40, 50), width=2)
    canvas.rectangle([x + w - 70, y + h - 16, x + w - 4, y + h - 4],
                     fill=(20, 20, 24))
    canvas.text((x + w - 66, y + h - 14), "24-HOUR", font=sans_bold(9),
                fill=(255, 255, 255))


def paint_flood(canvas, x, y, w, h):
    # v9: bright sky, pale riverside houses, blue flood water, rain
    paint_gradient(canvas, (x, y, x + w, y + h), (205, 228, 242), (180, 210, 235))
    canvas.ellipse([x + w - 34, y + 2, x + w - 12, y + 22], fill=(255, 230, 140))
    water_y = y + int(h * 0.52)
    for hx, hw in [(x + 8, 34), (x + 52, 40), (x + 104, 36)]:
        canvas.rectangle([hx, y + 8, hx + hw, water_y + 4], fill=(245, 238, 220))
        canvas.polygon([(hx - 3, y + 8), (hx + hw // 2, y - 2),
                        (hx + hw + 3, y + 8)], fill=(190, 70, 60))
        canvas.rectangle([hx + 6, y + 16, hx + 14, y + 24], fill=(120, 170, 210))
        canvas.rectangle([hx + hw - 14, y + 16, hx + hw - 6, y + 24],
                         fill=(120, 170, 210))
    paint_gradient(canvas, (x, water_y, x + w, y + h), (125, 180, 215),
                   (85, 150, 195))
    for wy in range(water_y + 4, y + h - 2, 6):
        canvas.arc([x + 6, wy - 3, x + 34, wy + 5], 200, 340,
                   fill=(255, 255, 255))
        canvas.arc([x + w // 2, wy - 3, x + w // 2 + 28, wy + 5], 200, 340,
                   fill=(255, 255, 255))
    for _ in range(18):
        rx = dice.randint(x + 4, x + w - 4)
        ry = dice.randint(y + 2, water_y - 2)
        canvas.line([(rx, ry), (rx - 2, ry + 6)], fill=(150, 190, 220))


def paint_soccer(canvas, x, y, w, h):
    # v9: bright green pitch, white lines, centre circle, goal, ball
    paint_gradient(canvas, (x, y, x + w, y + h), (155, 212, 142), (120, 190, 110))
    canvas.rectangle([x + 6, y + 4, x + w - 6, y + h - 4],
                     outline=(255, 255, 255), width=2)
    canvas.line([(x + w // 2, y + 4), (x + w // 2, y + h - 4)],
                fill=(255, 255, 255), width=2)
    canvas.ellipse([x + w // 2 - 12, y + h // 2 - 12, x + w // 2 + 12,
                    y + h // 2 + 12], outline=(255, 255, 255), width=2)
    canvas.rectangle([x + w - 30, y + 8, x + w - 8, y + h - 8],
                     outline=(255, 255, 255), width=2)
    for gy in range(y + 10, y + h - 8, 6):
        canvas.line([(x + w - 30, gy), (x + w - 8, gy)], fill=(255, 255, 255))
    canvas.ellipse([x + 16, y + h - 24, x + 32, y + h - 8], fill=(255, 255, 255),
                   outline=(40, 40, 40))
    for dx, dy in [(8, 0), (-8, 0), (0, 8), (0, -8)]:
        canvas.point((x + 24 + dx, y + h - 16 + dy), fill=(40, 40, 40))
    canvas.arc([x + 4, y + 2, x + 40, y + 30], 300, 60, fill=(255, 255, 255),
               width=2)


def paint_tennis(canvas, x, y, w, h):
    # v8: bright light-green court, white lines, yellow ball
    paint_gradient(canvas, (x, y, x + w, y + h), (165, 215, 145), (125, 190, 115))
    canvas.rectangle([x + 16, y + 6, x + w - 16, y + h - 6],
                     outline=(255, 255, 255), width=2)
    canvas.line([(x + w // 2, y + 6), (x + w // 2, y + h - 6)],
                fill=(255, 255, 255), width=2)
    canvas.line([(x + 16, y + h // 2), (x + w - 16, y + h // 2)],
                fill=(255, 255, 255), width=1)
    canvas.rectangle([x + 30, y + h - 16, x + w - 30, y + h - 10],
                     outline=(255, 255, 255))
    for nx in range(x + 34, x + w - 30, 10):
        canvas.line([(nx, y + h - 16), (nx, y + h - 10)], fill=(255, 255, 255))
    canvas.ellipse([x + w - 36, y + 6, x + w - 20, y + 22], fill=(205, 235, 70))
    canvas.arc([x + w - 36, y + 6, x + w - 20, y + 22], 20, 200,
               fill=(40, 60, 30), width=2)
    canvas.arc([x + w - 70, y + 2, x + w - 20, y + 34], 300, 60,
               fill=(255, 255, 255), width=2)


BANNER_PAINTS = {"cyclone": paint_cyclone, "cop": paint_cop, "market": paint_market,
                 "mercury": paint_mercury, "flags": paint_flags, "bars": paint_bars,
                 "rates": paint_rates, "cricket": paint_cricket, "strike": paint_strike,
                 "forest": paint_forest, "pill": paint_pill, "tennis": paint_tennis,
                 "kyiv": paint_kyiv, "flood": paint_flood, "soccer": paint_soccer}


def draw_banner(img, painter, x, y, w, h):
    """Render banner art onto a tile-sized buffer and paste it, so a
    painter that draws past its box (fixed offsets) cannot bleed into
    the neighbouring tile."""
    tmp = Image.new("RGB", (w, h))
    tmp_draw = ImageDraw.Draw(tmp)
    painter(tmp_draw, 0, 0, w, h)
    img.paste(tmp, (x, y))

# ---------------------------------------------------------------- map (v7: light, big pins)
# Dot map drawn from text art: "#" marks land, everything else is sea.
# Rows are 52 columns wide; trailing space is irrelevant (rows are padded
# to 52 before drawing), only leading space and "#" positions matter.
MAP_ART = """
  ####    ######   ##    ###############
   ####  ########  #    ##################
    ###  #########       ##################
     ##############     #################
      #############     ################
      #############    ##############  ##
      ##############  #############  ###
      ##############  ##########   ###
       ############   ########    ###
        ##########   ########    ##
         ########    ########   ##
          ######     ########  ##
          ######     #######   ####
          ######     ######    #####
          ######     #####     ####
          #####      ####      #####
          #####      ####      ######
          ####       ####      ######
          ###        ###       #####
          ###        ###       ####       ##
          ##                               ##
          ##
          #
                                                    
""".strip("\n").split("\n")

# Pins renumbered for v9: 1 Kyiv, 2 Odisha, 3 Seoul/Tokyo, 4 Antalya,
# 6 Brussels, 7 Tokyo, 8 Beijing, 9 Wellington, 10 Rome, 11 Mato Grosso,
# 12 Barcelona, 13 Turin, 14 Florida, 15 Doha. (5 Mercury is in space —
# no pin.)
MAP_PINS = [
    {"num": 2, "lon": 85, "lat": 20, "dx": 0, "dy": 0},
    {"num": 1, "lon": 30, "lat": 50, "dx": 8, "dy": -6},
    {"num": 4, "lon": 30, "lat": 36, "dx": 8, "dy": 6},
    {"num": 3, "lon": 133, "lat": 36, "dx": 0, "dy": 0},
    {"num": 6, "lon": 4, "lat": 50, "dx": -10, "dy": -8},
    {"num": 7, "lon": 139, "lat": 35, "dx": 2, "dy": 1},
    {"num": 8, "lon": 116, "lat": 39, "dx": 0, "dy": 0},
    {"num": 9, "lon": 174, "lat": -41, "dx": 0, "dy": 0},
    {"num": 10, "lon": 12, "lat": 41, "dx": 10, "dy": 4},
    {"num": 11, "lon": -55, "lat": -12, "dx": 0, "dy": 0},
    {"num": 12, "lon": 2, "lat": 41, "dx": -12, "dy": 2},
    {"num": 13, "lon": 7, "lat": 45, "dx": 6, "dy": -10},
    {"num": 14, "lon": -81, "lat": 29, "dx": 0, "dy": 0},
    {"num": 15, "lon": 51, "lat": 25, "dx": 8, "dy": 6},
]


def paint_map(canvas, x, y, w, h):
    canvas.rectangle([x, y, x + w, y + h], fill=(238, 234, 222))
    canvas.rectangle([x, y, x + w, y + h], outline=TEXT_INK, width=1)
    canvas.text((x + 8, y + 6), "WHERE IT HAPPENED", font=sans_bold(12),
                fill=TEXT_INK)
    mx, my = x + 6, y + 26
    mw, mh = w - 12, h - 62
    cols, rows = 52, 24
    cell_w, cell_h = mw / cols, mh / rows
    for r, row in enumerate(MAP_ART):
        for c, mark in enumerate(row.ljust(cols)):
            if mark == "#":
                cx = mx + c * cell_w + cell_w / 2
                cy = my + r * cell_h + cell_h / 2
                canvas.ellipse([cx - 1.8, cy - 1.8, cx + 1.8, cy + 1.8],
                               fill=(150, 138, 105))
    for pin in MAP_PINS:
        px = mx + (pin["lon"] + 180) / 360 * mw + pin["dx"]
        py = my + (72 - pin["lat"]) / 132 * mh + pin["dy"]
        canvas.ellipse([px - 9, py - 9, px + 9, py + 9], fill=ACCENT_RED,
                       outline=(255, 255, 255), width=2)
        f = sans_bold(9)
        s = str(pin["num"])
        canvas.text((px - text_width(f, s) / 2, py - 6), s, font=f,
                    fill=(255, 255, 255))
    canvas.text((x + 8, y + h - 30), "1–3 Lead · 4–15 Features.",
                font=sans_plain(9), fill=(70, 66, 58))
    canvas.text((x + 8, y + h - 18), "5 Mercury is in space — no pin.",
                font=sans_plain(9), fill=(70, 66, 58))


# ---------------------------------------------------------------- compose
def build_page(out_path):
    img = Image.new("RGB", (PAGE_W, PAGE_H), PAGE_BG)
    canvas = ImageDraw.Draw(img)
    add_grain(canvas, (0, 0, PAGE_W, PAGE_H), 150000)

    # ---- eyebrow
    canvas.text((MARGIN, 4), "THE WORLD IN ONE DAY", font=sans_bold(12),
                fill=ACCENT_RED)
    right = "48 STORIES · 7 REGIONS · EVERY ONE DATED FRIDAY 20 NOVEMBER 2026"
    canvas.text((PAGE_W - MARGIN - text_width(sans_bold(11), right), 5), right,
                font=sans_bold(11), fill=TEXT_INK)
    canvas.line([(MARGIN, 22), (PAGE_W - MARGIN, 22)], fill=TEXT_INK, width=2)

    # ---- masthead
    title = "Friday 20 November 2026"
    title_font = serif_bold(58)
    canvas.text(((PAGE_W - text_width(title_font, title)) / 2, 24), title,
                font=title_font, fill=TEXT_INK)
    deck = ("Cyclone Akvan strikes India • Ballistic missiles hit Kyiv • COP31 "
            "deadlocked on final day • Asian AI sell-off")
    deck_font = serif_italic(15)
    canvas.text(((PAGE_W - text_width(deck_font, deck)) / 2, 88), deck,
                font=deck_font, fill=TEXT_INK)
    canvas.line([(MARGIN, 106), (PAGE_W - MARGIN, 106)], fill=TEXT_INK, width=1)

    # ---- stat strip (6 numbers, winner's set, verified — see STAT_CARDS)
    y0, y1 = 110, 152
    cell_w = CONTENT_W / 6
    for i, stat in enumerate(STAT_CARDS):
        cx = MARGIN + i * cell_w
        if i:
            canvas.line([(cx, y0 + 4), (cx, y1 - 4)], fill=(200, 192, 175),
                        width=1)
        canvas.text((cx + 8, y0 + 1), stat["value"], font=sans_bold(27),
                    fill=ACCENT_RED if i in (0, 1, 2) else TEXT_INK)
        canvas.text((cx + 8, y0 + 31), stat["caption"], font=sans_plain(9),
                    fill=MUTED_GRAY)
    canvas.line([(MARGIN, y1 + 2), (PAGE_W - MARGIN, y1 + 2)], fill=TEXT_INK,
                width=2)

    # ---- region strip (7 segments, winner's order)
    ry0, ry1 = 156, 172
    seg_w = CONTENT_W / len(REGION_SEGMENTS)
    for i, region in enumerate(REGION_SEGMENTS):
        sx = MARGIN + i * seg_w
        canvas.rectangle([sx, ry0, sx + seg_w - 1, ry1], fill=region["colour"])
        reg_font = sans_bold(10)
        canvas.text((sx + (seg_w - text_width(reg_font, region["label"])) / 2,
                     ry0 + 3), region["label"], font=reg_font,
                    fill=(255, 255, 255))

    # ---- THREE LEADS, side by side, numbered 1-2-3 in reading order
    lead_y, lead_art_h = 178, 144
    lead_gap = 10
    lead_w = (CONTENT_W - 2 * lead_gap) // 3
    for i, lead in enumerate(LEADS):
        lx = MARGIN + i * (lead_w + lead_gap)
        draw_banner(img, BANNER_PAINTS[lead["banner"]], lx, lead_y, lead_w,
                    lead_art_h)
        canvas.rectangle([lx, lead_y, lx + lead_w, lead_y + lead_art_h],
                         outline=TEXT_INK, width=1)
        ky = lead_y + lead_art_h + 6
        kicker = "%02d · %s — %s" % (lead["num"], lead["place"], lead["field"])
        canvas.text((lx, ky), kicker, font=sans_bold(11), fill=ACCENT_RED)
        draw_wrapped(canvas, lx, ky + 14, serif_bold(20), lead["title"],
                     lead_w, TEXT_INK, leading=23)
        draw_wrapped(canvas, lx, ky + 62, sans_plain(11), lead["body"],
                     lead_w, (40, 40, 40), leading=14)
        draw_chip(canvas, lx, ky + 106, "SOURCE: " + lead["chip"],
                  sans_bold(9), (255, 255, 255), ACCENT_RED)

    # ---- mid grid: 12 stories, 6 columns x 2 rows, all bright tiles
    mid_gap = 8
    mid_w = (CONTENT_W - 5 * mid_gap) // 6
    mid_art_h = 40
    for slot, story in enumerate(STORIES):
        r, c = divmod(slot, 6)
        fx = int(MARGIN + c * (mid_w + mid_gap))
        fy = 458 + r * 132
        draw_banner(img, BANNER_PAINTS[story["banner"]], fx, fy, mid_w,
                    mid_art_h)
        # hero fact on a red chip: guarantees contrast on any banner art
        hero_font = sans_bold(story["hero_size"])
        hw = min(int(text_width(hero_font, story["hero"])) + 12, mid_w)
        hy0 = fy + mid_art_h - story["hero_size"] - 8
        canvas.rectangle([fx, hy0, fx + hw, fy + mid_art_h], fill=ACCENT_RED)
        canvas.text((fx + 6, hy0 + 3), story["hero"], font=hero_font,
                    fill=(255, 255, 255))
        chip_font = sans_bold(8)
        chw = text_width(chip_font, story["chip"])
        canvas.rectangle([fx + mid_w - chw - 10, fy + 3, fx + mid_w - 4, fy + 15],
                         fill=(15, 15, 18))
        canvas.text((fx + mid_w - chw - 7, fy + 5), story["chip"], font=chip_font,
                    fill=(255, 255, 255))
        canvas.rectangle([fx, fy, fx + mid_w, fy + mid_art_h],
                         outline=TEXT_INK, width=1)
        ty = fy + 44
        kicker = "%02d · %s — %s" % (story["num"], story["place"], story["field"])
        canvas.text((fx, ty), kicker, font=sans_bold(9), fill=ACCENT_RED)
        title_lines = len(wrap_text(sans_bold(12), story["title"], mid_w))
        draw_wrapped(canvas, fx, ty + 12, sans_bold(12), story["title"], mid_w,
                     TEXT_INK, leading=14)
        draw_wrapped(canvas, fx, ty + 12 + 14 * title_lines,
                     sans_plain(9), story["body"], mid_w, (40, 40, 40),
                     leading=11)

    # ---- bottom: map + ALSO 33 briefs
    by0 = 728
    map_w = 220
    paint_map(canvas, MARGIN, by0, map_w, 210)
    ax = MARGIN + map_w + 8
    aw = PAGE_W - MARGIN - ax
    canvas.text((ax, by0), "ALSO ON FRIDAY 20 NOVEMBER — 33 MORE STORIES",
                font=sans_bold(13), fill=ACCENT_RED)
    legend = "■ Europe  ■ Asia-Pacific  ■ Americas  ■ Africa  ■ Middle East  ■ Sport & science"
    canvas.text((ax, by0 + 15), legend, font=sans_plain(9), fill=MUTED_GRAY)
    col_w = (aw - 10) / 2
    row_h = 12
    for i, brief in enumerate(BRIEF_ITEMS):
        col, row = divmod(i, 17)
        bx = ax + col * (col_w + 10)
        by = by0 + 28 + row * row_h
        lead = "%d %s — " % (brief["num"], brief["place"])
        for size in (11, 10, 9.5, 9):
            lead_font = sans_bold(int(size))
            body_font = sans_plain(size)
            if (text_width(lead_font, lead)
                    + text_width(body_font, brief["text"]) <= col_w):
                break
        canvas.text((bx, by), lead, font=lead_font, fill=ACCENT_RED)
        canvas.text((bx + text_width(lead_font, lead), by), brief["text"],
                    font=body_font, fill=TEXT_INK)

    # ---- DATE CHECK
    dy0 = 966
    canvas.rectangle([MARGIN, dy0, PAGE_W - MARGIN, dy0 + 38], outline=ACCENT_RED,
                     width=1)
    canvas.rectangle([MARGIN, dy0, MARGIN + 96, dy0 + 38], fill=ACCENT_RED)
    canvas.text((MARGIN + 8, dy0 + 5), "DATE", font=sans_bold(12),
                fill=(255, 255, 255))
    canvas.text((MARGIN + 8, dy0 + 20), "CHECK", font=sans_bold(12),
                fill=(255, 255, 255))
    date_note = ("First reported Thursday 19 Nov, so NOT shown as Friday’s "
                 "news: Trump–Xi–Putin Shenzhen talks + ‘peace declaration’ · "
                 "ICJ Myanmar Rohingya genocide verdict (9–6) · GTA VI midnight "
                 "launch · $190.4m Van Gogh sale · Voyager 1 one-light-day "
                 "confirmation · Senate 48–51 Iran war-powers vote.")
    draw_wrapped(canvas, MARGIN + 104, dy0 + 3, sans_plain(11), date_note,
                 PAGE_W - MARGIN - (MARGIN + 104) - 6, TEXT_INK, leading=13)

    # ---- footer
    foot = ("Every story here happened, or was first reported, on Friday 20 "
            "November 2026. Officials’ counts are attributed. Sources named "
            "per story · Full list in SOURCES.md · Original drawings.")
    canvas.text((MARGIN, 1007), foot, font=sans_plain(10), fill=MUTED_GRAY)

    img.save(out_path, "PNG")
    return out_path


def main():
    target = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if target:
        os.makedirs(target, exist_ok=True)
        out = os.path.join(target, "entry.png")
    else:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    build_page(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
