[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/haidildariell/news-image-20261120-v9/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/haidildariell/news-image-20261120-v9/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

# news-image-20261120 v9 — The World in One Day (Friday 20 November 2026)

One 1024×1024 image summing up the world's news of Friday 20 November 2026:
48 stories, every fact sourced in `SOURCES.md`, all drawings original.

## Run

```sh
python3 build_image.py        # draws entry.png (needs Pillow, local only)
MAKEFUN_OUTPUT_DIR=out python3 main.py   # copies entry.png to out/
python3 main.py               # copies entry.png to /output (grader default)
```

`main.py` is standard library only: it copies the pre-rendered `entry.png`
to `$MAKEFUN_OUTPUT_DIR` (default `/output`). It must stay that way — the
grader runs it in stock `python:3.13-slim`, which has no Pillow. The image
itself is drawn by `build_image.py` with Pillow (no network, deterministic
— two runs write identical bytes). Fonts resolve from the system DejaVu /
Liberation paths with a built-in fallback.

## Design (v9)

v8 stands at #493/17.248, judge 983.928 (12W/0D/0L, provisional), 5.286 pts
below the #50 paid line (989.214, "48 stories, 15 illustrated"). v9 keeps
the v8 winning template untouched and attacks the gap with breadth, the way
the #50 and #100 entries do:

- **Same template** — three bright leads numbered 1-2-3 (Kyiv, Cyclone
  Akvan, AI sell-off), the winner's six-number stat strip, region bar in
  the winner's order, light pin map, DATE CHECK box. No dark hero, no dark
  tiles.
- **48 stories (up from 37)** — 11 new briefs (38–48), each verified
  against a named source in `SOURCES.md` (Poland missiles, Kharkiv
  counter-offensive, Crimean Bridge, €1bn EU aid, US–China military-AI
  agreement, Fiji drought disaster, and five more). Nothing invented: any
  story that could not be verified was dropped, not guessed.
- **15 illustrated panels (up from 13)** — the mid grid is now 6×2
  (tiles 4–15). Two former briefs are promoted to illustrated tiles:
  Florida's record St Johns River flood (18.3 ft) and Australia's 2–0
  U17 World Cup upset of Argentina, each with a new original drawing.
- **Strict reading-order numbering** — leads 1–3, mid 4–15, briefs 16–48.
  Region bar recounts to 48: Europe 14, Asia-Pacific 10, Middle East 5,
  Africa 3, Americas 8, Oceania 6, Global 2.
- **Banner art is clipped to its tile** — each banner is rendered onto a
  tile-sized buffer before pasting, so no painter can bleed into its
  neighbour (v8's forest painter drew past its box).

Kept from v8: masthead + 4-story deck, "48 stories · 7 regions" kicker,
light pin map with big numbered pins (now 14 pins: Florida and Doha join),
source chip per story, red bold lead-ins in the 33 briefs.

## Facts

48 stories (see `SOURCES.md`). The stat strip's 300,000+ is a lower
bound of the sourced 370,000 evacuated ahead of Akvan.
