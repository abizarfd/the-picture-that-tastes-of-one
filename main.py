#!/usr/bin/env python3
"""A Bowl of Ramen, Steam Rising - pure stdlib rasterizer + PNG writer."""
import math, os, random, struct, zlib

W = H = 1024
buf = bytearray(W * H * 3)
_cache = {}
def cb(r, g, b):
    k = (r, g, b)
    v = _cache.get(k)
    if v is None:
        v = bytes(k); _cache[k] = v
    return v

def span(y, x0, x1, r, g, b):
    if y < 0 or y >= H: return
    if x0 < 0: x0 = 0
    if x1 > W: x1 = W
    if x1 <= x0: return
    n = x1 - x0
    i = (y * W + x0) * 3
    buf[i:i + n * 3] = cb(r, g, b) * n

def ellipse(cx, cy, rx, ry, r, g, b):
    if rx <= 0 or ry <= 0: return
    y0 = max(0, cy - ry); y1 = min(H - 1, cy + ry)
    for y in range(y0, y1 + 1):
        t = (y - cy) / ry
        d = 1.0 - t * t
        if d <= 0: continue
        dx = int(rx * math.sqrt(d))
        span(y, cx - dx, cx + dx + 1, r, g, b)

def disc(cx, cy, rad, r, g, b):
    ellipse(cx, cy, rad, rad, r, g, b)

def rect(x0, y0, x1, y1, r, g, b):
    y0 = max(0, y0); y1 = min(H, y1)
    for y in range(y0, y1):
        span(y, x0, x1, r, g, b)

def blend_disc(cx, cy, rad, r, g, b, alpha):
    # low-alpha soft disc, bounded box only
    x0 = max(0, cx - rad); x1 = min(W - 1, cx + rad)
    y0 = max(0, cy - rad); y1 = min(H - 1, cy + rad)
    a = alpha; ia = 1.0 - a
    for y in range(y0, y1 + 1):
        dy = y - cy
        base = y * W * 3
        for x in range(x0, x1 + 1):
            dx = x - cx
            if dx * dx + dy * dy > rad * rad: continue
            i = base + x * 3
            buf[i] = int(buf[i] * ia + r * a)
            buf[i+1] = int(buf[i+1] * ia + g * a)
            buf[i+2] = int(buf[i+2] * ia + b * a)

def thick_line(x0, y0, x1, y1, rad, r, g, b):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for s in range(steps + 1):
        t = s / steps
        disc(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), rad, r, g, b)

def arc_points(cx, cy, rx, ry, a0, a1, n):
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        pts.append((int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a))))
    return pts

rng = random.Random(7)

# --- background: warm dark wood gradient ---
for y in range(H):
    t = y / (H - 1)
    r = int(66 - 26 * t); g = int(38 - 16 * t); b = int(22 - 10 * t)
    i = y * W * 3
    buf[i:i + W * 3] = cb(r, g, b) * W

# --- soft warm glow behind bowl: many tiny steps, no rings ---
for s in range(44, 0, -1):
    f = s / 44.0
    # interpolate glow colour -> background-ish at edge
    r = int(52 + 78 * (1 - f)); g = int(30 + 42 * (1 - f)); b = int(18 + 18 * (1 - f))
    ellipse(512, 470, int(430 * f), int(330 * f), r, g, b)

# --- table shadow under bowl ---
ellipse(512, 830, 380, 55, 22, 12, 7)

# --- bowl: dark ceramic, big ---
ellipse(512, 610, 375, 215, 74, 18, 16)          # outer body
ellipse(512, 600, 375, 205, 96, 24, 20)          # body lighter top
ellipse(512, 585, 350, 185, 128, 38, 28)         # rim ring
ellipse(512, 585, 330, 168, 52, 14, 12)          # rim inner shadow

# --- broth: amber/gold, layered ellipses for depth ---
ellipse(512, 580, 322, 160, 176, 108, 28)
ellipse(512, 575, 300, 145, 204, 132, 38)
ellipse(512, 570, 272, 128, 226, 158, 52)
ellipse(512, 565, 235, 108, 240, 178, 70)

# --- noodle swirls: many overlapping curved strokes ---
yellows = [(248, 214, 110), (232, 186, 74), (255, 230, 150), (214, 164, 58), (242, 200, 92)]
for _ in range(46):
    cx = rng.randint(330, 690); cy = rng.randint(490, 660)
    rx = rng.randint(28, 78); ry = rng.randint(14, 34)
    a0 = rng.uniform(0, 6.28); a1 = a0 + rng.uniform(1.2, 3.6)
    col = rng.choice(yellows); rad = rng.randint(5, 9)
    for (px, py) in arc_points(cx, cy, rx, ry, a0, a1, 22):
        # keep noodles inside broth ellipse roughly
        if ((px - 512) / 300.0) ** 2 + ((py - 572) / 138.0) ** 2 > 0.92: continue
        disc(px, py, rad, *col)
# a few straight-ish noodle strands across centre
for _ in range(10):
    x0 = rng.randint(360, 560); y0 = rng.randint(520, 620)
    thick_line(x0, y0, x0 + rng.randint(60, 140), y0 + rng.randint(-18, 18),
               rng.randint(5, 7), *rng.choice(yellows))

# --- chashu pork: two slices, pink-brown with pale fat ring ---
for (cx, cy) in [(400, 620), (455, 545)]:
    ellipse(cx, cy, 78, 52, 198, 118, 92)
    ellipse(cx - 6, cy - 4, 62, 40, 228, 178, 148)
    ellipse(cx - 6, cy - 4, 46, 28, 196, 112, 86)
    ellipse(cx - 6, cy - 4, 30, 17, 214, 140, 108)

# --- halved soft egg, centre-right, big glossy yolk ---
ellipse(648, 568, 88, 62, 252, 242, 214)
ellipse(648, 568, 74, 50, 246, 232, 198)
ellipse(648, 570, 50, 40, 255, 138, 18)
ellipse(648, 570, 42, 32, 255, 166, 40)
disc(632, 552, 12, 255, 205, 105)   # yolk highlight

# --- nori: dark sheet at bowl edge, left ---
rect(238, 500, 318, 612, 18, 38, 24)
ellipse(278, 500, 40, 10, 18, 38, 24)
ellipse(278, 612, 40, 10, 18, 38, 24)

# --- chopped green onions: bright rings/dots scattered ---
for _ in range(42):
    x = rng.randint(300, 724); y = rng.randint(470, 690)
    if ((x - 512) / 300.0) ** 2 + ((y - 572) / 138.0) ** 2 > 0.88: continue
    if (x - 648) ** 2 / 88 ** 2 + (y - 568) ** 2 / 62 ** 2 < 0.8: continue
    disc(x, y, rng.randint(6, 9), 46, 168, 62)
    disc(x, y, rng.randint(3, 4), 150, 230, 120)

# --- red chili threads ---
for _ in range(7):
    x0 = rng.randint(380, 640); y0 = rng.randint(500, 640)
    thick_line(x0, y0, x0 + rng.randint(28, 55), y0 + rng.randint(-10, 14), 3, 205, 32, 22)

# --- glossy sheen arc on broth, top-left ---
for (px, py) in arc_points(512, 572, 250, 112, 3.5, 4.6, 26):
    disc(px, py, 7, 255, 214, 120)

# --- steam: smooth sine wisps, opaque muted tan (no alpha overlap beads) ---
# Drawn as one continuous thick line per wisp so there are no dotted artefacts.
for base_x, phase, amp in [(430, 0.0, 26), (512, 1.4, 30), (595, 2.6, 24)]:
    pts = []
    for s in range(120):
        t = s / 119.0
        y = int(500 - t * 330)
        x = int(base_x + math.sin(t * 5.2 + phase) * amp * (0.4 + t))
        pts.append((x, y))
    for i in range(len(pts) - 1):
        thick_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], 9, 172, 130, 86)
    for i in range(len(pts) - 1):
        thick_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], 4, 205, 164, 116)

# --- chopsticks resting diagonally across rim ---
for off in (-16, 16):
    # tapered: draw in segments, radius shrinking toward tip (right end)
    x0, y0, x1, y1 = 268, 452 + off, 768, 668 + off
    steps = 60
    for s in range(steps + 1):
        t = s / steps
        x = int(x0 + (x1 - x0) * t); y = int(y0 + (y1 - y0) * t)
        rad = int(11 - 5 * t)
        if t > 0.82:
            disc(x, y, rad, 96, 58, 26)      # darker tip
        else:
            disc(x, y, rad, 184, 132, 72)    # warm wood
    # thin darker edge line along lower side
    thick_line(x0 + 4, y0 + 9, x1 - 8, y1 + 7, 2, 120, 82, 40)

# --- PNG writer: colour type 2, filter 0 ---
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(out_dir, exist_ok=True)
raw = bytearray()
for y in range(H):
    raw.append(0)
    raw += buf[y * W * 3:(y + 1) * W * 3]
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
       + chunk(b"IEND", b""))
with open(os.path.join(out_dir, "entry.png"), "wb") as f:
    f.write(png)
print("wrote", os.path.join(out_dir, "entry.png"), len(png), "bytes")
