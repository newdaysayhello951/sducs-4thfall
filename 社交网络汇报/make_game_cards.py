# -*- coding: utf-8 -*-
"""Draw three flat icon cards for the three games cited in Table 6."""
import os
from PIL import Image, ImageDraw, ImageFont

FIG = r"C:\Users\86134\Desktop\大四上\社交网络汇报\figs"
W, H = 1200, 760

CJK = r"C:\Windows\Fonts\msyh.ttc"
CJK_B = r"C:\Windows\Fonts\msyhbd.ttc"
LAT = r"C:\Windows\Fonts\segoeui.ttf"
LAT_B = r"C:\Windows\Fonts\segoeuib.ttf"


def font(path, size):
    for p in (path, CJK):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def new_card(tint):
    im = Image.new("RGB", (W, H), tint)
    return im, ImageDraw.Draw(im)


def ink(rgb, a=255):
    return rgb


# ---------- 1) Overcooked! 2 : pot + steam + board ----------
def draw_cooking():
    im, d = new_card((0xFA, 0xF3, 0xE6))
    C = (0xB8, 0x7A, 0x1E)
    cx, cy = W // 2, 300
    # steam
    for dx in (-70, 0, 70):
        x = cx + dx
        d.arc([x - 26, cy - 210, x + 26, cy - 158], 200, 340, fill=C, width=9)
        d.arc([x - 26, cy - 168, x + 26, cy - 116], 200, 340, fill=C, width=9)
    # lid
    d.rounded_rectangle([cx - 130, cy - 130, cx + 130, cy - 108], 10, fill=C)
    d.ellipse([cx - 22, cy - 152, cx + 22, cy - 122], fill=C)
    # body
    d.rounded_rectangle([cx - 150, cy - 100, cx + 150, cy + 60], 26, outline=C, width=11)
    # handles
    d.rounded_rectangle([cx - 196, cy - 50, cx - 148, cy - 16], 12, fill=C)
    d.rounded_rectangle([cx + 148, cy - 50, cx + 196, cy - 16], 12, fill=C)
    # board + cleaver
    d.rounded_rectangle([cx - 250, cy + 120, cx - 30, cy + 190], 16, outline=C, width=10)
    d.line([cx - 210, cy + 165, cx - 90, cy + 165], fill=C, width=7)
    d.rounded_rectangle([cx + 70, cy + 148, cx + 208, cy + 196], 9, fill=C)
    d.rounded_rectangle([cx + 212, cy + 160, cx + 268, cy + 184], 10, fill=C)
    # text
    d.text((W // 2, 600), "Overcooked! 2", font=font(LAT_B, 62), fill=(0x1A, 0x23, 0x32),
           anchor="mm")
    d.text((W // 2, 672), "合作烹饪 · 工序链 + 共用设备", font=font(CJK, 34),
           fill=(0x5B, 0x65, 0x73), anchor="mm")
    im.save(os.path.join(FIG, "game_1_cooking.png"))


# ---------- 2) Big Pharma : capsule + pills ----------
def draw_pharma():
    im, d = new_card((0xEE, 0xF5, 0xF2))
    C = (0x1E, 0x7A, 0x4B)
    cx, cy = W // 2, 300
    # capsule (upper)
    d.rounded_rectangle([cx - 190, cy - 200, cx + 190, cy - 74], 63, outline=C, width=12)
    d.line([cx, cy - 196, cx, cy - 78], fill=C, width=11)
    # small pills both sides
    d.ellipse([cx - 320, cy - 190, cx - 236, cy - 106], outline=C, width=9)
    d.line([cx - 300, cy - 170, cx - 256, cy - 126], fill=C, width=8)
    d.ellipse([cx + 236, cy - 196, cx + 318, cy - 114], outline=C, width=9)
    d.line([cx + 254, cy - 178, cx + 300, cy - 132], fill=C, width=8)
    # three machines sitting on the belt
    for dx in (-215, 0, 215):
        x = cx + dx
        d.rounded_rectangle([x - 62, cy - 40, x + 62, cy + 78], 14, outline=C, width=10)
        d.line([x - 32, cy + 20, x + 32, cy + 20], fill=C, width=8)
    # conveyor
    d.line([cx - 340, cy + 150, cx + 340, cy + 150], fill=C, width=10)
    for x in range(cx - 320, cx + 330, 64):
        d.ellipse([x - 12, cy + 138, x + 12, cy + 162], outline=C, width=7)
    d.text((W // 2, 600), "Big Pharma", font=font(LAT_B, 62), fill=(0x1A, 0x23, 0x32),
           anchor="mm")
    d.text((W // 2, 672), "工厂建造 · 专用设备 + 每步耗时", font=font(CJK, 34),
           fill=(0x5B, 0x65, 0x73), anchor="mm")
    im.save(os.path.join(FIG, "game_2_pharma.png"))


# ---------- 3) Construction Simulator : excavator ----------
def draw_construction():
    im, d = new_card((0xEE, 0xF2, 0xF8))
    C = (0x1F, 0x5A, 0xC0)
    cx, cy = W // 2 - 40, 310
    # tracks
    d.rounded_rectangle([cx - 200, cy + 90, cx + 60, cy + 158], 34, outline=C, width=12)
    d.line([cx - 160, cy + 124, cx + 20, cy + 124], fill=C, width=9)
    # body
    d.rounded_rectangle([cx - 170, cy + 6, cx + 20, cy + 92], 16, outline=C, width=11)
    # cab
    d.rounded_rectangle([cx - 60, cy - 58, cx + 20, cy + 8], 12, outline=C, width=10)
    d.line([cx - 22, cy - 52, cx - 22, cy + 2], fill=C, width=7)
    # boom
    d.line([cx + 10, cy + 30, cx + 210, cy - 110], fill=C, width=15, joint="curve")
    # stick
    d.line([cx + 210, cy - 110, cx + 330, cy + 20], fill=C, width=14, joint="curve")
    # bucket (solid)
    ex, ey = cx + 330, cy + 20
    d.polygon([(ex, ey), (ex + 62, ey + 54), (ex + 38, ey + 100),
               (ex - 34, ey + 88), (ex - 28, ey + 40)], fill=C)
    # ground
    d.line([cx - 250, cy + 168, cx + 430, cy + 168], fill=(0xB9, 0xC3, 0xD2), width=8)
    d.text((W // 2, 600), "Construction Simulator", font=font(LAT_B, 58),
           fill=(0x1A, 0x23, 0x32), anchor="mm")
    d.text((W // 2, 672), "工程机械 · 长链工序 + 专用设备", font=font(CJK, 34),
           fill=(0x5B, 0x65, 0x73), anchor="mm")
    im.save(os.path.join(FIG, "game_3_construction.png"))


draw_cooking()
draw_pharma()
draw_construction()
print("done")
