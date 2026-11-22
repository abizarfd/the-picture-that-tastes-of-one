#!/usr/bin/env python3
"""Molten Chocolate Lava Cake, Still Warm.

A make.fun entry rendered with the Python standard library only.
No third-party packages, no network, no external files: a tiny
software renderer draws the scene into an RGB byte buffer and
a hand-written PNG encoder writes it out.
"""

import math
import os
import random
import struct
import zlib

W = 1024
H = 1024
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

# The picture: one bytearray, three bytes per pixel, row major.
buf = bytearray(W * H * 3)


def _lerp(a, b, t):
    return int(a + (b - a) * t)


def _mix(c1, c2, t):
    return (_lerp(c1[0], c2[0], t), _lerp(c1[1], c2[1], t),
            _lerp(c1[2], c2[2], t))


def hline(y, x0, x1, color):
    """Fill a horizontal run of pixels on row y (clipped)."""
    if y < 0 or y >= H:
        return
    if x0 < 0:
        x0 = 0
    if x1 >= W:
        x1 = W - 1
    if x1 < x0:
        return
    n = x1 - x0 + 1
    base = (y * W + x0) * 3
    buf[base:base + n * 3] = bytes(color) * n


def vline(x, y0, y1, color, width=1):
    for xx in range(x - width // 2, x + width // 2 + 1):
        for y in range(y0, y1 + 1):
            if 0 <= xx < W and 0 <= y < H:
                base = (y * W + xx) * 3
                buf[base:base + 3] = bytes(color)


def ellipse(cx, cy, rx, ry, color, clip=None):
    """Filled ellipse by scanlines, optionally clipped to another ellipse.

    clip is (ccx, ccy, crx, cry); each row span is intersected with the
    clip ellipse's span on the same row, so highlights stay inside the cake.
    """
    if rx <= 0 or ry <= 0:
        return
    y0 = max(0, cy - ry)
    y1 = min(H - 1, cy + ry)
    for y in range(y0, y1 + 1):
        dy = (y - cy) / ry
        rem = 1.0 - dy * dy
        if rem < 0.0:
            continue
        dx = int(rx * math.sqrt(rem))
        x0, x1 = cx - dx, cx + dx
        if clip is not None:
            ccx, ccy, crx, cry = clip
            cdy = (y - ccy) / cry
            crem = 1.0 - cdy * cdy
            if crem < 0.0:
                continue
            cdx = int(crx * math.sqrt(crem))
            x0 = max(x0, ccx - cdx)
            x1 = min(x1, ccx + cdx)
        hline(y, x0, x1, color)


def disc(cx, cy, r, color, clip=None):
    ellipse(cx, cy, r, r, color, clip)


def blend_disc(cx, cy, r, color, alpha):
    """Soft translucent disc: per-pixel blend, bounded box only."""
    if r <= 0:
        return
    inv = 255 - alpha
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        dy = y - cy
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        for x in range(max(0, cx - dx), min(W, cx + dx + 1)):
            base = (y * W + x) * 3
            buf[base] = (color[0] * alpha + buf[base] * inv) // 255
            buf[base + 1] = (color[1] * alpha + buf[base + 1] * inv) // 255
            buf[base + 2] = (color[2] * alpha + buf[base + 2] * inv) // 255


def speckle(rng, cx, cy, rx, ry, n, colors, rmin=1, rmax=3):
    """Deterministic scatter of tiny dots inside an ellipse."""
    for _ in range(n):
        ang = rng.uniform(0.0, 2.0 * math.pi)
        rad = math.sqrt(rng.random())
        x = int(cx + rad * rx * 0.96 * math.cos(ang))
        y = int(cy + rad * ry * 0.96 * math.sin(ang))
        disc(x, y, rng.randint(rmin, rmax), rng.choice(colors),
             clip=(cx, cy, rx, ry))


def write_png(path):
    """Minimal PNG writer: signature, IHDR, IDAT, IEND, CRC32."""
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter byte: none
        raw += buf[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


def main():
    rng = random.Random(20261122)
    cx, cy = 512, 620          # cake dome centre
    dome = (cx, cy, 272, 262)  # dome ellipse, used as a clip region

    # --- Background: warm vertical gradient, dark top, glowing middle. ---
    top = (26, 14, 8)
    mid = (64, 36, 19)
    bot = (22, 12, 7)
    for y in range(H):
        t = y / (H - 1)
        if t < 0.55:
            c = _mix(top, mid, t / 0.55)
        else:
            c = _mix(mid, bot, (t - 0.55) / 0.45)
        hline(y, 0, W - 1, c)

    # Warm glow behind the cake: many small-step nested ellipses so the
    # falloff reads as one soft halo instead of visible rings.
    for i in range(9):
        t = i / 8.0
        ellipse(cx, 560, 400 - i * 22, 350 - i * 20,
                _mix((64, 36, 19), (98, 53, 24), t))

    # --- Steam wisps above the crater (soft, faint). ---
    for wx, phase in ((452, 0.0), (512, 2.1), (572, 4.2)):
        for k in range(7):
            y = 350 - k * 18
            x = int(wx + 16 * math.sin(phase + k * 0.55))
            blend_disc(x, y, 12 - k, (215, 195, 170), 18)

    # --- Plate shadow, then the wide white plate near the bottom. ---
    ellipse(512, 852, 415, 92, (16, 9, 5))
    ellipse(512, 842, 405, 96, (168, 156, 140))   # rim thickness
    ellipse(512, 832, 405, 96, (246, 239, 228))   # plate top
    ellipse(512, 832, 338, 74, (208, 198, 186))   # rim ring
    ellipse(512, 832, 322, 67, (246, 239, 228))   # plate inner field

    # --- Cake dome: dark edges, warm-lit top-left. ---
    ellipse(*dome, (58, 31, 17))
    ellipse(cx - 58, cy - 72, 205, 180, (104, 56, 27), clip=dome)
    ellipse(cx - 78, cy - 92, 150, 128, (132, 74, 36), clip=dome)
    ellipse(cx - 92, cy - 108, 96, 78, (158, 96, 48), clip=dome)
    ellipse(cx + 96, cy + 88, 150, 120, (44, 23, 12), clip=dome)
    # Baked crust speckle, darker and lighter crumbs.
    speckle(rng, cx, cy, 272, 262, 520,
            [(38, 20, 10), (96, 52, 25), (140, 78, 38), (28, 15, 8)])
    # Soft top-left sheen, kept small so it reads as light, not a cap.
    ellipse(cx - 110, cy - 130, 92, 56, (175, 110, 55), clip=dome)
    ellipse(cx - 118, cy - 138, 54, 30, (200, 135, 72), clip=dome)

    # --- Ganache drips over the dome edge. Each drip starts on the dome
    # surface (computed from the dome ellipse), never floating above it.
    for dx, length, w in ((-176, 80, 9), (-138, 100, 7), (128, 122, 8),
                          (168, 140, 10), (196, 62, 6)):
        x = cx + dx
        surf = int(cy - 262 * math.sqrt(max(
            0.0, 1.0 - ((x - cx) / 272.0) ** 2)))
        vline(x, surf + 4, surf + length, (32, 16, 8), width=w)
        vline(x - w // 2, surf + 4, surf + length, (86, 44, 20), width=2)
        disc(x, surf + length, w // 2 + 1, (32, 16, 8))

    # --- Molten crater at the dome top: rings to a glowing core. ---
    crater = (512, 412)
    ellipse(crater[0], crater[1], 112, 44, (38, 19, 9))
    ellipse(crater[0], crater[1], 90, 35, (118, 54, 18))
    ellipse(crater[0], crater[1], 66, 26, (198, 102, 30))
    ellipse(crater[0], crater[1], 42, 17, (255, 168, 58))
    ellipse(crater[0], crater[1], 22, 9, (255, 216, 132))
    disc(crater[0] - 6, crater[1] - 2, 5, (255, 236, 180))

    # --- Molten river down the front, wavy centreline, bright core. ---
    path = []
    for k in range(41):
        t = k / 40.0
        y = int(428 + t * 400)
        x = int(512 + 20 * math.sin(t * 5.2) + 8 * t)
        path.append((x, y, t))
    for layer, col, rad in ((0, (150, 66, 18), 34),
                            (1, (205, 105, 30), 25),
                            (2, (240, 160, 70), 14)):
        for x, y, t in path:
            r = int(rad * (0.75 + 0.45 * t))
            disc(x, y, r, col)
    # Glossy highlight stripe along the river's left edge.
    for x, y, t in path[4:38]:
        disc(x - 16, y, 3, (255, 205, 120))

    # --- Molten pool on the plate, in front of the dome. ---
    ellipse(512, 862, 118, 34, (168, 76, 19))
    ellipse(512, 860, 92, 26, (218, 116, 33))
    ellipse(512, 858, 56, 15, (255, 184, 88))
    ellipse(506, 856, 30, 7, (255, 220, 140))

    # --- Two raspberries, front-right, with drupelets. ---
    for bx, by, br in ((682, 788, 50), (622, 828, 43)):
        disc(bx, by, br + 4, (110, 12, 30))
        disc(bx, by, br, (168, 22, 48))
        for _ in range(46):
            ang = rng.uniform(0.0, 2.0 * math.pi)
            rad = math.sqrt(rng.random())
            x = int(bx + rad * (br - 8) * math.cos(ang))
            y = int(by + rad * (br - 8) * math.sin(ang))
            disc(x, y, rng.randint(3, 6),
                 rng.choice([(205, 52, 88), (228, 84, 112), (150, 18, 44)]),
                 clip=(bx, by, br, br))
        disc(bx - 14, by - 16, 7, (240, 120, 140))
        disc(bx + 8, by + 10, 4, (120, 14, 34))

    # --- Two mint leaves, front-left, with pale veins. ---
    for lx, ly, rx, ry in ((332, 812, 64, 23), (382, 848, 60, 21)):
        ellipse(lx, ly, rx + 4, ry + 4, (22, 88, 44))
        ellipse(lx, ly, rx, ry, (52, 148, 76))
        hline(ly, lx - rx + 8, lx + rx - 8, (178, 228, 178))
        for k in range(-3, 4):
            xx = lx + k * 14
            yy = ly + (k * 2 if k >= 0 else -k * 2)
            disc(xx, yy, 2, (178, 228, 178))
        disc(lx - 20, ly - 6, 5, (120, 205, 130))

    # --- Powdered-sugar dusting on the plate and a whisper on the dome. ---
    for _ in range(340):
        x = rng.randint(150, 874)
        y = int(832 + rng.uniform(-1, 1)
                * 62 * math.sqrt(max(0.0, 1 - ((x - 512) / 380.0) ** 2)))
        if 760 <= y <= 905:
            disc(x, y, rng.randint(1, 2), (252, 247, 238))
    speckle(rng, cx, cy - 150, 200, 90, 45,
            [(248, 242, 232), (240, 232, 220)], rmin=1, rmax=2)

    # --- Vignette: small dark corners only, plus a darker top strip. ---
    for ccx, ccy in ((-40, -40), (1064, -40), (-40, 1064), (1064, 1064)):
        ellipse(ccx, ccy, 200, 180, (14, 8, 4))
    for y in range(0, 70):
        hline(y, 0, W - 1, _mix((14, 8, 4), (26, 14, 8), y / 70.0))

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "entry.png")
    size = write_png(path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
