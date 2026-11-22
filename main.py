"""Molten Chocolate Lava Cake, Still Warm — make.fun entry.

Draws a single 1024x1024 PNG of a molten chocolate lava cake on a white
ceramic plate: dark warm background, glowing molten crater, a glossy river
of chocolate running down the dome, raspberries and mint on the plate,
faint steam above. Pure Pillow, deterministic (fixed seed), no network,
no external files, no text in the image.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
OUT = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"), "entry.png")
RNG = random.Random(20261122)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(size, top, bottom):
    """Vertical linear gradient."""
    w, h = size
    img = Image.new("RGB", (1, h))
    px = img.load()
    for y in range(h):
        px[0, y] = lerp(top, bottom, y / max(h - 1, 1))
    return img.resize((w, h))


def radial_glow(size, centre, radius, colour, peak):
    """Soft radial glow: `peak` alpha at centre fading to 0 at `radius`."""
    glow = Image.new("L", size, 0)
    d = ImageDraw.Draw(glow)
    steps = 48
    for i in range(steps, 0, -1):
        t = i / steps
        r = radius * t
        a = int(peak * (1 - t) ** 1.6)
        d.ellipse(
            [centre[0] - r, centre[1] - r * 0.62,
             centre[0] + r, centre[1] + r * 0.62],
            fill=a,
        )
    layer = Image.new("RGB", size, colour)
    return glow, layer


def main():
    # ---- background: dark warm vertical gradient -------------------------
    img = vgrad((W, H), (38, 20, 10), (16, 9, 5)).convert("RGBA")

    # warm glow behind the plate / cake
    glow_mask, glow_img = radial_glow((W, H), (512, 640), 430, (146, 84, 32), 110)
    img.paste(glow_img, (0, 0), glow_mask)

    # ---- plate shadow, then the wide white ceramic plate -----------------
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    ds.ellipse([140, 830, 884, 950], fill=(0, 0, 0, 130))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(18)))

    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dp = ImageDraw.Draw(plate)
    # body / thickness of the plate
    dp.ellipse([132, 700, 892, 900], fill=(178, 168, 152, 255))
    dp.ellipse([132, 688, 892, 888], fill=(214, 205, 190, 255))
    # top surface
    dp.ellipse([132, 676, 892, 876], fill=(247, 242, 233, 255))
    # rim line
    dp.ellipse([168, 700, 856, 852], outline=(203, 192, 175, 255), width=4)
    dp.ellipse([196, 716, 828, 836], outline=(226, 216, 200, 255), width=3)
    img = Image.alpha_composite(img, plate)

    # sheen arc, top-left of the plate
    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dsh = ImageDraw.Draw(sheen)
    dsh.arc([180, 690, 700, 860], start=150, end=250,
            fill=(255, 255, 255, 90), width=14)
    img = Image.alpha_composite(img, sheen.filter(ImageFilter.GaussianBlur(6)))

    # ---- the cake dome ----------------------------------------------------
    cx, cy, rx, ry = 512, 560, 252, 246
    dome = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dome)
    dark = (43, 20, 8)
    light = (150, 88, 36)
    steps = 70
    for i in range(steps):
        t = i / (steps - 1)
        # shrink toward a light point up-left of centre as we brighten
        sx = cx - 46 * t
        sy = cy - 52 * t
        srx = rx * (1 - 0.62 * t)
        sry = ry * (1 - 0.62 * t)
        dd.ellipse([sx - srx, sy - sry, sx + srx, sy + sry],
                   fill=lerp(dark, light, t ** 1.35) + (255,))
    # baked-crumb speckle, kept inside the dome silhouette
    mask = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(mask)
    dm.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    speck = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dsp = ImageDraw.Draw(speck)
    for _ in range(1500):
        ang = RNG.uniform(0, math.tau)
        rr = math.sqrt(RNG.random())
        x = cx + math.cos(ang) * rr * rx * 0.97
        y = cy + math.sin(ang) * rr * ry * 0.97
        r = RNG.uniform(0.8, 2.2)
        if RNG.random() < 0.55:
            col = (20, 10, 4, RNG.randint(70, 130))
        else:
            col = (214, 150, 84, RNG.randint(40, 90))
        dsp.ellipse([x - r, y - r, x + r, y + r], fill=col)
    dome = Image.alpha_composite(dome, speck)
    dome.putalpha(Image.composite(dome.split()[3], Image.new("L", (W, H), 0), mask))
    img = Image.alpha_composite(img, dome.filter(ImageFilter.GaussianBlur(1.2)))

    # ---- molten crater at the top of the dome -----------------------------
    crater = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dc = ImageDraw.Draw(crater)
    ccx, ccy = 512, 392
    rings = [
        ((26, 12, 5, 255), 100, 44),
        ((74, 34, 12, 255), 84, 36),
        ((146, 66, 16, 255), 66, 28),
        ((214, 110, 26, 255), 48, 20),
        ((255, 166, 52, 255), 32, 13),
        ((255, 214, 120, 255), 18, 8),
    ]
    for col, rxx, ryy in rings:
        dc.ellipse([ccx - rxx, ccy - ryy, ccx + rxx, ccy + ryy], fill=col)
    # small warm glossy highlight on the molten surface
    dc.ellipse([ccx - 24, ccy - 16, ccx + 6, ccy - 4],
               fill=(255, 200, 110, 80))
    img = Image.alpha_composite(img, crater.filter(ImageFilter.GaussianBlur(3)))

    # ---- glossy molten river down the front, pooling on the plate --------
    river = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(river)
    # wavy band from the crater to the plate
    top_y, bot_y = 400, 848
    left, right = [], []
    for y in range(top_y, bot_y + 1, 8):
        wob = 18 * math.sin((y - top_y) / 90.0) + 8 * math.sin((y - top_y) / 31.0)
        half = 38 + 18 * (y - top_y) / (bot_y - top_y)
        left.append((512 - half + wob, y))
        right.append((512 + half + wob, y))
    dr.polygon(left + right[::-1], fill=(122, 56, 16, 255))
    # brighter inner flow
    left2, right2 = [], []
    for y in range(top_y + 6, bot_y - 6, 8):
        wob = 18 * math.sin((y - top_y) / 90.0) + 8 * math.sin((y - top_y) / 31.0)
        half = 22 + 9 * (y - top_y) / (bot_y - top_y)
        left2.append((512 - half + wob, y))
        right2.append((512 + half + wob, y))
    dr.polygon(left2 + right2[::-1], fill=(196, 96, 26, 255))
    # pool on the plate
    dr.ellipse([392, 800, 632, 884], fill=(146, 68, 20, 255))
    dr.ellipse([430, 816, 594, 868], fill=(214, 116, 34, 255))
    dr.ellipse([462, 826, 562, 856], fill=(255, 176, 74, 255))
    img = Image.alpha_composite(img, river.filter(ImageFilter.GaussianBlur(2)))
    # gloss streaks on the river
    gloss = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(gloss)
    dg.line([(486, 470), (472, 700)], fill=(255, 200, 110, 150), width=7)
    dg.line([(540, 500), (552, 760)], fill=(255, 190, 100, 120), width=5)
    dg.line([(500, 830), (540, 830)], fill=(255, 210, 130, 110), width=5)
    img = Image.alpha_composite(img, gloss.filter(ImageFilter.GaussianBlur(2)))

    # ---- thin ganache drips over the dome edge ----------------------------
    drips = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd2 = ImageDraw.Draw(drips)
    for x, y0, length, wdt in [
        (330, 395, 70, 13), (392, 344, 60, 11), (636, 346, 75, 13),
        (688, 384, 55, 11),
    ]:
        dd2.rounded_rectangle([x - wdt // 2, y0, x + wdt // 2, y0 + length],
                              radius=wdt // 2, fill=(38, 18, 7, 255))
        dd2.rounded_rectangle([x - wdt // 2, y0 + length - 4,
                               x + wdt // 2, y0 + length + 8],
                              radius=wdt // 2, fill=(38, 18, 7, 255))
        # thin highlight on each drip
        dd2.line([(x - wdt // 2 + 2, y0 + 4), (x - wdt // 2 + 2, y0 + length)],
                 fill=(150, 90, 40, 170), width=2)
    img = Image.alpha_composite(img, drips.filter(ImageFilter.GaussianBlur(0.8)))

    # ---- raspberries, front-right ------------------------------------------
    def raspberry(bx, by, r):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=(168, 16, 52, 255))
        for _ in range(26):
            ang = RNG.uniform(0, math.tau)
            rr = math.sqrt(RNG.random()) * r * 0.72
            px = bx + math.cos(ang) * rr
            py = by + math.sin(ang) * rr
            pr = r * RNG.uniform(0.16, 0.24)
            shade = RNG.choice([(214, 40, 84), (232, 84, 116), (140, 10, 44)])
            d.ellipse([px - pr, py - pr, px + pr, py + pr],
                      fill=shade + (255,))
            d.ellipse([px - pr * 0.4, py - pr * 0.5,
                       px + pr * 0.1, py - pr * 0.1],
                      fill=(255, 170, 190, 120))
        d.ellipse([bx - r * 0.5, by - r * 0.55, bx - r * 0.15, by - r * 0.3],
                  fill=(255, 200, 210, 70))
        return lay

    img = Image.alpha_composite(img, raspberry(706, 748, 52))
    img = Image.alpha_composite(img, raspberry(634, 796, 42))

    # ---- mint leaves, front-left -------------------------------------------
    def mint_leaf(bx, by, length, width, angle_deg):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.ellipse([bx - length // 2, by - width // 2,
                   bx + length // 2, by + width // 2],
                  fill=(46, 130, 62, 255))
        d.ellipse([bx - length // 2 + 6, by - width // 2 + 5,
                   bx + length // 2 - 10, by + width // 2 - 6],
                  fill=(74, 168, 88, 255))
        # centre vein + side veins
        d.line([(bx - length // 2 + 4, by), (bx + length // 2 - 4, by)],
               fill=(214, 240, 190, 200), width=3)
        for t in (-0.5, 0.0, 0.5):
            vx = bx + t * length * 0.5
            d.line([(vx, by), (vx + 12, by - width // 2 + 8)],
                   fill=(214, 240, 190, 140), width=2)
            d.line([(vx, by), (vx + 12, by + width // 2 - 8)],
                   fill=(214, 240, 190, 140), width=2)
        return lay.rotate(angle_deg, center=(bx, by), resample=Image.BICUBIC)

    img = Image.alpha_composite(img, mint_leaf(300, 786, 118, 46, -24))
    img = Image.alpha_composite(img, mint_leaf(348, 822, 104, 42, 14))

    # ---- powdered sugar dusting on the plate --------------------------------
    sugar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dsu = ImageDraw.Draw(sugar)
    for _ in range(700):
        x = RNG.uniform(170, 854)
        y = RNG.uniform(700, 862)
        # keep sugar on the plate ellipse, off the cake and river
        if ((x - 512) / 380) ** 2 + ((y - 776) / 100) ** 2 > 1:
            continue
        if ((x - 512) / 252) ** 2 + ((y - 560) / 246) ** 2 < 1.05:
            continue
        if 430 < x < 600 and y > 780:
            continue
        r = RNG.uniform(0.7, 1.8)
        dsu.ellipse([x - r, y - r, x + r, y + r],
                    fill=(255, 255, 255, RNG.randint(90, 190)))
    img = Image.alpha_composite(img, sugar)

    # ---- faint steam wisps above the cake ----------------------------------
    steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dst = ImageDraw.Draw(steam)
    for sx, phase, amp in [(452, 0.0, 26), (512, 1.4, 32), (572, 2.6, 24)]:
        pts = []
        for y in range(360, 150, -6):
            t = (360 - y) / 210.0
            pts.append((sx + amp * math.sin(t * 4.2 + phase) * (0.4 + t),
                        y))
        dst.line(pts, fill=(255, 240, 220, 26), width=9)
    img = Image.alpha_composite(img, steam.filter(ImageFilter.GaussianBlur(10)))

    # ---- dark vignette at the corners ---------------------------------------
    vig = Image.new("L", (W, H), 0)
    dv = ImageDraw.Draw(vig)
    for i in range(60, 0, -1):
        t = i / 60
        a = int(120 * (1 - t) ** 2)
        dv.ellipse([512 - 720 * t, 512 - 720 * t,
                    512 + 720 * t, 512 + 720 * t], outline=a, width=26)
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img.paste(black, (0, 0), vig)

    # ---- save ---------------------------------------------------------------
    img.convert("RGB").save(OUT, optimize=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
