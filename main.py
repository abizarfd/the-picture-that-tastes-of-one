#!/usr/bin/env python3
"""Molten Chocolate Lava Cake, Still Warm -- make.fun entry.

Pure Python standard library only (math, os, random, struct, zlib).
Own scanline rasterizer + own PNG writer. Deterministic (fixed seed).
Writes entry.png into $MAKEFUN_OUTPUT_DIR (default /output).
"""
import math
import os
import random
import struct
import zlib

W = 1024
H = 1024
random.seed(42)

buf = bytearray(W * H * 3)


def fill_span(y, x0, x1, rgb):
    if y < 0 or y >= H:
        return
    if x0 < 0:
        x0 = 0
    if x1 > W - 1:
        x1 = W - 1
    if x1 < x0:
        return
    n = x1 - x0 + 1
    s = (y * W + x0) * 3
    buf[s:s + n * 3] = bytes(rgb) * n


def erows(cx, cy, rx, ry):
    """Yield (y, x0, x1) rows of an ellipse."""
    for y in range(cy - ry, cy + ry + 1):
        if y < 0 or y >= H:
            continue
        t = (y - cy) / ry
        hw = int(rx * math.sqrt(max(0.0, 1.0 - t * t)))
        yield y, cx - hw, cx + hw


def fill_ellipse(cx, cy, rx, ry, rgb):
    for y, x0, x1 in erows(cx, cy, rx, ry):
        fill_span(y, x0, x1, rgb)


def disc(cx, cy, r, rgb):
    fill_ellipse(cx, cy, r, r, rgb)


def dot(x, y, r, rgb):
    if r <= 1:
        if 0 <= x < W and 0 <= y < H:
            s = (y * W + x) * 3
            buf[s:s + 3] = bytes(rgb)
        return
    disc(x, y, r, rgb)


def thick_line(x0, y0, x1, y1, w, rgb):
    dist = math.hypot(x1 - x0, y1 - y0)
    steps = max(1, int(dist / max(2, w // 3)))
    r = max(1, w // 2)
    for i in range(steps + 1):
        t = i / steps
        dot(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), r, rgb)


def lerp(a, b, t):
    return int(a + (b - a) * t)


def lerp_rgb(c0, c1, t):
    return (lerp(c0[0], c1[0], t), lerp(c0[1], c1[1], t), lerp(c0[2], c1[2], t))


# ---------------------------------------------------------------- background
# Warm mid-brown vertical gradient, lifted so the dish separates from it.
TOP = (132, 78, 42)
MID = (116, 64, 34)
BOT = (72, 40, 20)
for y in range(H):
    if y < 512:
        c = lerp_rgb(TOP, MID, y / 512.0)
    else:
        c = lerp_rgb(MID, BOT, (y - 512) / 512.0)
    fill_span(y, 0, W - 1, c)

# ------------------------------------------------- smooth halo (banded spans)
# 22 nested spans per row, alpha steps ~2% -- no visible rings.
GX, GY, GR = 512, 430, 370
GLOW = (255, 168, 86)
NB = 22
for y in range(GY - GR, GY + GR + 1):
    if y < 0 or y >= H:
        continue
    if y < 512:
        bg = lerp_rgb(TOP, MID, y / 512.0)
    else:
        bg = lerp_rgb(MID, BOT, (y - 512) / 512.0)
    dy = y - GY
    for k in range(NB, 0, -1):
        r = GR * k / NB
        if abs(dy) >= r:
            continue
        hw = int(math.sqrt(r * r - dy * dy))
        a = 0.55 * (1.0 - (k - 0.5) / NB) ** 1.5
        fill_span(y, GX - hw, GX + hw, lerp_rgb(bg, GLOW, a))

# --------------------------------------------------------------------- plate
# Soft shadow, then a big cream plate near the bottom (~78% of frame width).
fill_ellipse(512, 876, 412, 100, (46, 22, 10))
fill_ellipse(512, 862, 402, 94, (248, 240, 228))
fill_ellipse(512, 860, 362, 78, (232, 222, 206))
fill_ellipse(512, 860, 348, 71, (246, 238, 226))

# ---------------------------------------------------------------------- dome
# Big hero dome: centre (512,480), rx 335 -> 670 px wide (~65% of frame).
CX, CY, RX, RY = 512, 480, 335, 305
DOME_TOP = (196, 132, 74)
DOME_MID = (160, 98, 50)
DOME_BOT = (104, 58, 28)
for y, x0, x1 in erows(CX, CY, RX, RY):
    t = (y - (CY - RY)) / (2.0 * RY)
    if t < 0.5:
        c = lerp_rgb(DOME_TOP, DOME_MID, t * 2.0)
    else:
        c = lerp_rgb(DOME_MID, DOME_BOT, (t - 0.5) * 2.0)
    fill_span(y, x0, x1, c)

# One very subtle warm patch, top-left -- barely lighter than the dome
# gradient there, so no visible ring edge.
fill_ellipse(428, 322, 200, 140, (188, 124, 68))

# Rim-light crescent along the top-left dome edge.
prev = None
for deg in range(196, 288, 3):
    a = math.radians(deg)
    px = int(CX + RX * math.cos(a))
    py = int(CY + RY * math.sin(a))
    if prev is not None:
        thick_line(prev[0], prev[1], px, py, 9, (255, 204, 128))
    prev = (px, py)
prev = None
for deg in range(200, 284, 3):
    a = math.radians(deg)
    px = int(CX + (RX - 4) * math.cos(a))
    py = int(CY + (RY - 4) * math.sin(a))
    if prev is not None:
        thick_line(prev[0], prev[1], px, py, 4, (255, 226, 168))
    prev = (px, py)

# ------------------------------------------------- crumb speckle (thousands)
SPECK_DARK = [(66, 36, 14), (84, 46, 20), (96, 54, 24)]
SPECK_MID = [(150, 94, 48), (168, 110, 60), (132, 80, 40)]
SPECK_LIGHT = [(216, 162, 96), (232, 180, 112), (198, 142, 82)]
for _ in range(5200):
    x = random.randint(CX - RX, CX + RX)
    y = random.randint(CY - RY, CY + RY)
    dx = (x - CX) / RX
    dy = (y - CY) / RY
    if dx * dx + dy * dy > 0.96:
        continue
    r = random.random()
    if r < 0.42:
        c = random.choice(SPECK_DARK)
    elif r < 0.78:
        c = random.choice(SPECK_MID)
    else:
        c = random.choice(SPECK_LIGHT)
    s = 1 if random.random() < 0.72 else 2
    if s == 1:
        dot(x, y, 1, c)
    else:
        fill_span(y, x, x + 1, c)
        fill_span(y + 1, x, x + 1, c)

# ------------------------------------------------------- cracks (radiating)
# Dark irregular cracked lines radiating out from the crater rim.
CRATER_CX, CRATER_CY = 512, 382
for _ in range(14):
    ang = random.uniform(0, 2 * math.pi)
    # Start near the crater rim, walk outward across the dome top.
    x = CRATER_CX + 150 * math.cos(ang)
    y = CRATER_CY + 52 * math.sin(ang) - 6
    length = random.randint(55, 130)
    steps = length // 6
    a = ang
    for _ in range(steps):
        nx = x + 6 * math.cos(a)
        ny = y + 6 * math.sin(a)
        thick_line(int(x), int(y), int(nx), int(ny), 4, (52, 24, 8))
        x, y = nx, ny
        a += random.uniform(-0.45, 0.45)

# ------------------------------------------------------- ganache drips
# Wide (20-26 px), short, dark brown with a lighter highlight stripe each.
def drip(x, top, length, w):
    fill_ellipse(x, top, w // 2, w // 2, (96, 48, 22))
    for y in range(top, top + length):
        fill_span(y, x - w // 2, x + w // 2, (96, 48, 22))
    disc(x, top + length, w // 2, (96, 48, 22))
    # highlight stripe, slightly left of centre
    hx = x - w // 4
    for y in range(top + 2, top + length - 2):
        fill_span(y, hx - 2, hx + 1, (168, 104, 52))

drip(296, 246, 62, 22)
drip(378, 204, 74, 24)
drip(648, 210, 68, 22)
drip(728, 248, 58, 26)
drip(798, 322, 52, 20)

# ------------------------------------------------------------- molten crater
# Thick glossy dark rim, then an irregular (wobbled) molten pool.
fill_ellipse(CRATER_CX, CRATER_CY, 170, 64, (52, 24, 10))
fill_ellipse(CRATER_CX, CRATER_CY, 160, 58, (74, 34, 12))
POOL_TOP = (214, 96, 18)
POOL_MID = (255, 176, 52)
POOL_HOT = (255, 222, 96)
for y in range(CRATER_CY - 54, CRATER_CY + 55):
    t = (y - (CRATER_CY - 54)) / 108.0
    base = 152 * math.sqrt(max(0.0, 1.0 - ((y - CRATER_CY) / 54.0) ** 2))
    wob = 1.0 + 0.04 * math.sin(y * 0.21 + 1.3) + 0.03 * math.sin(y * 0.53)
    hw = int(base * wob)
    if t < 0.5:
        c = lerp_rgb(POOL_TOP, POOL_MID, t * 2.0)
    else:
        c = lerp_rgb(POOL_MID, POOL_HOT, (t - 0.5) * 2.0)
    fill_span(y, CRATER_CX - hw, CRATER_CX + hw, c)
# Brightest heart of the pool + specular dots.
fill_ellipse(CRATER_CX, CRATER_CY + 2, 82, 26, (255, 216, 92))
fill_ellipse(CRATER_CX - 6, CRATER_CY, 52, 15, (255, 232, 140))
for (sx, sy, sr) in ((478, 372, 4), (540, 390, 3), (512, 366, 3),
                     (556, 374, 2), (466, 390, 2)):
    disc(sx, sy, sr, (255, 244, 190))

# ------------------------------------------------- overflow tongues + river
# Two thick glossy tongues spilling from the crater down the dome.
def tongue(x0, y_top, y_bot, w0, w1, phase):
    # Same molten colours as the river, so the tongue merges into it;
    # rounded end so it never reads as a cut-off strip.
    for y in range(y_top, y_bot + 1):
        t = (y - y_top) / max(1, y_bot - y_top)
        cx = x0 + int(10 * math.sin(y * 0.03 + phase))
        hw = int((w0 + (w1 - w0) * t) * (1.0 + 0.06 * math.sin(y * 0.11 + phase)))
        c = lerp_rgb((228, 112, 26), (246, 152, 46),
                     (y - RIVER_TOP) / (RIVER_BOT - RIVER_TOP))
        fill_span(y, cx - hw, cx + hw, c)
        fill_span(y, cx - hw + 10, cx - hw + 22, (255, 196, 94))

RIVER_TOP, RIVER_BOT = 430, 850

tongue(452, 408, 560, 26, 34, 0.7)
tongue(578, 414, 540, 22, 30, 2.1)

# Wide irregular river: narrow at the crater, widening to the plate, wavy.
for y in range(RIVER_TOP, RIVER_BOT + 1):
    t = (y - RIVER_TOP) / (RIVER_BOT - RIVER_TOP)
    cx = 512 + int(16 * math.sin((y - RIVER_TOP) * 0.013) + 7 * math.sin(y * 0.031))
    hw = int((34 + 26 * t) * (1.0 + 0.09 * math.sin(y * 0.05)))
    c = lerp_rgb((228, 112, 26), (246, 152, 46), t)
    fill_span(y, cx - hw, cx + hw, c)
    # glossy highlight stripe, left of centre
    fill_span(y, cx - hw + 10, cx - hw + 22, (255, 196, 94))
    # darker edge shade on the right
    fill_span(y, cx + hw - 7, cx + hw, (176, 72, 14))

# Big irregular glossy pool on the plate (300+ px wide).
fill_ellipse(512, 850, 158, 34, (226, 110, 26))
fill_ellipse(512, 848, 132, 27, (246, 150, 44))
fill_ellipse(512, 846, 96, 18, (255, 182, 74))
fill_ellipse(508, 842, 58, 10, (255, 212, 120))
# Bright highlight crescent on the pool.
prev = None
for deg in range(195, 330, 4):
    a = math.radians(deg)
    px = int(512 + 128 * math.cos(a))
    py = int(850 + 26 * math.sin(a))
    if prev is not None:
        thick_line(prev[0], prev[1], px, py, 4, (255, 226, 150))
    prev = (px, py)
for (sx, sy, sr) in ((470, 838, 3), (540, 856, 3), (516, 830, 2)):
    disc(sx, sy, sr, (255, 240, 180))

# ------------------------------------------------------------- mint leaves
# Pointed-oval leaves (lens profile), lighter centre, clear vein, tilted.
def leaf(cx, cy, length, width, ang_deg, flip):
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    hl = length // 2
    hw = width // 2
    for gy in range(cy - hw - 4, cy + hw + 5):
        for gx in range(cx - hl - 4, cx + hl + 5):
            dx, dy = gx - cx, gy - cy
            u = dx * ca + dy * sa          # along leaf axis
            v = -dx * sa + dy * ca         # across leaf axis
            if abs(u) > hl:
                continue
            prof = math.sin(math.pi * (u + hl) / length) ** 0.8
            if abs(v) > hw * prof:
                continue
            f = abs(v) / max(1.0, hw * prof)
            if abs(v) <= 2:
                c = (178, 224, 142)        # vein
            elif f < 0.45:
                c = lerp_rgb((112, 192, 92), (64, 140, 62), f / 0.45)
            else:
                c = lerp_rgb((64, 140, 62), (36, 102, 48), (f - 0.45) / 0.55)
            s = (gy * W + gx) * 3
            buf[s:s + 3] = bytes(c)

leaf(330, 806, 132, 54, -18, False)
leaf(404, 838, 118, 48, 12, False)
leaf(288, 846, 104, 44, -38, False)

# -------------------------------------------------------------- raspberries
# Bigger than v2, front-right on the plate; drupelet bumps + highlights.
def raspberry(cx, cy, r):
    fill_ellipse(cx, cy, r, r, (148, 18, 34))
    for _ in range(46):
        ang = random.uniform(0, 2 * math.pi)
        d = random.uniform(0, r * 0.82)
        bx = int(cx + d * math.cos(ang))
        by = int(cy + d * math.sin(ang))
        br = random.randint(5, 9)
        c = random.choice([(198, 28, 50), (218, 58, 72), (176, 24, 44),
                           (228, 78, 92)])
        disc(bx, by, br, c)
        dot(bx - 1, by - 1, 1, (255, 150, 160))
    for _ in range(8):
        ang = random.uniform(0, 2 * math.pi)
        d = random.uniform(0, r * 0.6)
        dot(int(cx + d * math.cos(ang)), int(cy + d * math.sin(ang)),
            2, (255, 190, 190))

raspberry(668, 792, 60)
raspberry(752, 758, 50)

# ------------------------------------------------------- sugar sparkles
for _ in range(90):
    x = random.randint(180, 844)
    y = random.randint(790, 920)
    if random.random() < 0.5:
        dot(x, y, 1, (255, 250, 240))
    else:
        fill_span(y, x, x + 1, (255, 246, 230))

# ---------------------------------------------------------------- PNG writer
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return c

raw = bytearray()
for y in range(H):
    raw.append(0)  # filter: None
    raw += buf[y * W * 3:(y + 1) * W * 3]

png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
png += chunk(b"IEND", b"")

outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(outdir, exist_ok=True)
with open(os.path.join(outdir, "entry.png"), "wb") as f:
    f.write(png)
