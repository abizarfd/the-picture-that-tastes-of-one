#!/usr/bin/env python3
"""Molten Chocolate Lava Cake, Still Warm.

One picture of food: a single molten chocolate lava cake on a white
ceramic plate, ganache dripping, centre spilling open, raspberries and
mint beside it, warm light from the top-left, dark warm background.
Procedural PIL only — deterministic, no network, no external files.
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png), 1024x1024.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
RNG = random.Random(20261122)

# ---------------------------------------------------------------- palette
BG_TOP = (46, 26, 18)
BG_BOT = (16, 8, 6)
PLATE = (244, 238, 228)
PLATE_SHADE = (196, 184, 168)
PLATE_RIM = (214, 204, 188)
CAKE_DARK = (38, 16, 8)
CAKE_MID = (74, 32, 14)
CAKE_TOP = (122, 58, 24)
GANACHE = (26, 10, 5)
MOLTEN = (96, 42, 14)
MOLTEN_HI = (168, 88, 30)
BERRY = (178, 18, 52)
BERRY_HI = (232, 72, 96)
MINT = (52, 128, 62)
MINT_LT = (110, 178, 96)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(size, top, bottom):
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(size[1]):
        c = lerp(top, bottom, y / max(1, size[1] - 1))
        for x in range(size[0]):
            px[x, y] = c
    return img


def soft_ellipse(draw, box, fill, blur):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(box, fill=fill + (255,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    draw._image.paste(Image.alpha_composite(draw._image.convert("RGBA"), layer).convert("RGB"), (0, 0))


def speckle(draw, box, n, colors, rmin=1, rmax=3):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x = RNG.uniform(x0, x1)
        y = RNG.uniform(y0, y1)
        r = RNG.uniform(rmin, rmax)
        c = RNG.choice(colors)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    img = vgrad((W, H), BG_TOP, BG_BOT)
    draw = ImageDraw.Draw(img, "RGBA")

    # Warm glow behind the plate, top-left light pool.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([120, 40, 900, 700], fill=(255, 176, 92, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # ---- table shadow under the plate
    draw.ellipse([212, 788, 812, 900], fill=(0, 0, 0, 110))

    # ---- white ceramic plate (wide ellipse, slight rim)
    draw.ellipse([168, 560, 856, 884], fill=PLATE_SHADE)
    draw.ellipse([180, 568, 844, 868], fill=PLATE)
    draw.ellipse([196, 580, 828, 852], outline=PLATE_RIM, width=4)
    # plate sheen, top-left
    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.ellipse([250, 590, 560, 700], fill=(255, 255, 255, 46))
    sheen = sheen.filter(ImageFilter.GaussianBlur(28))
    img = Image.alpha_composite(img.convert("RGBA"), sheen).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # ---- lava cake: big round dome, centre ~ (512, 560), radius ~ 250
    cx, cy, r = 512, 570, 252
    # body: concentric shading rings, dark edge -> warm top
    for i in range(60, 0, -1):
        t = i / 60.0
        rr = r * t
        c = lerp(CAKE_DARK, CAKE_TOP, (1 - t) ** 1.4)
        draw.ellipse([cx - rr, cy - rr * 0.92, cx + rr, cy + rr * 0.92], fill=c)
    # offset the dome light: warm cap shifted up-left
    cap = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cap)
    cd.ellipse([cx - 190, cy - 235, cx + 120, cy + 40], fill=(186, 104, 44, 120))
    cap = cap.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img.convert("RGBA"), cap).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # baked crumb texture on the dome
    speckle(draw, [cx - 200, cy - 200, cx + 200, cy + 130],
            700, [(52, 24, 10), (96, 46, 20), (140, 74, 32), (30, 12, 6)], 1, 3)
    # cocoa dusting, heavier top-left
    speckle(draw, [cx - 170, cy - 210, cx + 40, cy - 60],
            380, [(210, 170, 130), (235, 205, 175), (170, 120, 80)], 1, 2)

    # ---- molten centre: open crater at top, glossy spill
    crater = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    kd = ImageDraw.Draw(crater)
    kd.ellipse([cx - 132, cy - 228, cx + 132, cy - 64], fill=(24, 10, 4, 255))
    kd.ellipse([cx - 110, cy - 212, cx + 110, cy - 82], fill=(132, 58, 18, 255))
    kd.ellipse([cx - 78, cy - 196, cx + 76, cy - 100], fill=(196, 106, 36, 255))
    kd.ellipse([cx - 46, cy - 180, cx + 44, cy - 122], fill=(232, 150, 62, 255))
    crater = crater.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img.convert("RGBA"), crater).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # molten river flowing down the front of the cake onto the plate
    river = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(river)
    pts = [(cx - 58, cy - 130), (cx - 74, cy + 10), (cx - 52, cy + 150),
           (cx - 78, cy + 235), (cx - 30, cy + 268), (cx + 26, cy + 250),
           (cx + 62, cy + 200), (cx + 40, cy + 90), (cx + 58, cy - 40),
           (cx + 44, cy - 130)]
    rd.polygon(pts, fill=MOLTEN + (255,))
    rd.ellipse([cx - 96, cy + 218, cx + 96, cy + 292], fill=MOLTEN + (255,))
    rd.ellipse([cx - 62, cy + 232, cx + 60, cy + 282], fill=MOLTEN_HI + (255,))
    river = river.filter(ImageFilter.GaussianBlur(5))
    img = Image.alpha_composite(img.convert("RGBA"), river).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")
    # glossy streaks on the river
    draw.line([(cx - 34, cy - 100), (cx - 46, cy + 120)], fill=(214, 128, 58, 170), width=10)
    draw.line([(cx + 8, cy - 60), (cx - 2, cy + 150)], fill=(226, 148, 72, 150), width=7)
    draw.ellipse([cx - 40, cy + 238, cx + 8, cy + 268], fill=(226, 148, 72, 170))

    # ---- ganache drips over the dome edge (glossy dark chocolate)
    for bx, blen, bw in [(330, 96, 20), (392, 62, 16), (452, 122, 18),
                         (596, 78, 16), (660, 112, 18), (716, 66, 14)]:
        top = cy - 190 + (bx - cx) ** 2 / 900.0
        draw.rounded_rectangle([bx - bw // 2, top, bx + bw // 2, top + blen],
                               radius=bw // 2, fill=(58, 26, 10))
        draw.ellipse([bx - bw // 2, top + blen - bw // 2, bx + bw // 2, top + blen + bw // 2],
                     fill=(58, 26, 10))
        draw.line([(bx - bw // 4, top + 8), (bx - bw // 4, top + blen - 10)],
                  fill=(150, 84, 40, 220), width=4)

    # top gloss highlight on the dome
    hi = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hd.ellipse([cx - 200, cy - 250, cx - 20, cy - 130], fill=(255, 220, 170, 90))
    hi = hi.filter(ImageFilter.GaussianBlur(34))
    img = Image.alpha_composite(img.convert("RGBA"), hi).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # ---- raspberries (two, front-right on the plate)
    for bx, by, br in [(742, 700, 52), (688, 748, 42)]:
        draw.ellipse([bx - br, by - br, bx + br, by + br], fill=(120, 8, 30))
        for k in range(9):
            ang = k * math.tau / 9 + 0.35
            dx, dy = math.cos(ang) * br * 0.55, math.sin(ang) * br * 0.55
            draw.ellipse([bx + dx - 13, by + dy - 13, bx + dx + 13, by + dy + 13],
                         fill=BERRY)
            draw.ellipse([bx + dx - 7, by + dy - 9, bx + dx + 1, by + dy - 1],
                         fill=BERRY_HI)
        draw.ellipse([bx - br * 0.55, by - br * 0.6, bx - br * 0.05, by - br * 0.1],
                     fill=(240, 120, 140, 160))
    # ---- mint leaves (two, front-left)
    for lx, ly, ang in [(300, 742, -0.5), (352, 770, 0.35)]:
        leaf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(leaf)
        ld.ellipse([lx - 46, ly - 20, lx + 46, ly + 20], fill=MINT + (255,))
        ld.line([(lx - 42, ly), (lx + 42, ly)], fill=MINT_LT + (255,), width=4)
        for t in (-24, 0, 24):
            ld.line([(lx + t, ly), (lx + t + 10, ly - 12)], fill=MINT_LT + (255,), width=3)
        leaf = leaf.rotate(math.degrees(ang), center=(lx, ly), resample=Image.BICUBIC)
        img = Image.alpha_composite(img.convert("RGBA"), leaf).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # ---- steam wisps above the cake (soft, warm)
    steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(steam)
    for sx, sway, wdt in [(430, 14, 10), (512, -11, 12), (592, 10, 9)]:
        pts = []
        for i in range(21):
            y = 350 - i * 9
            x = sx + math.sin(i * 0.55) * sway
            pts.append((x, y))
        td.line(pts, fill=(255, 240, 220, 55), width=wdt, joint="curve")
    steam = steam.filter(ImageFilter.GaussianBlur(16))
    img = Image.alpha_composite(img.convert("RGBA"), steam).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # ---- powdered sugar dust on the plate rim
    speckle(draw, [240, 620, 780, 840], 260,
            [(250, 244, 232), (235, 225, 210)], 1, 2)

    # ---- vignette: darken corners so the eye stays on the cake
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-220, -220, W + 220, H + 220], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(180))
    black = Image.new("RGB", (W, H), (8, 4, 3))
    img = Image.composite(img, black, vig)

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    img.save(path, "PNG", optimize=True)
    print("wrote", path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
