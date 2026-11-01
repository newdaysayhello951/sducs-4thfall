# -*- coding: utf-8 -*-
"""案例二（Windows 11 右键菜单）示意图。"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = "figures"
os.makedirs(OUT, exist_ok=True)
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"


def F(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def R(d, box, r, fill=None, outline=None, width=2):
    x0, y0, x1, y1 = box
    r = int(min(r, (y1 - y0) / 2 - 1, (x1 - x0) / 2 - 1))
    d.rounded_rectangle(box, radius=max(r, 0), fill=fill, outline=outline, width=width)


def T(d, xy, text, size=22, bold=False, fill=(32, 32, 32)):
    d.text(xy, text, font=F(size, bold), fill=fill)


WIN_BG = (243, 243, 243)
MENU_BG = (252, 252, 252)
MENU_LINE = (228, 228, 228)
SEL_BG = (232, 232, 232)
BLUE = (0, 95, 184)
GREY = (96, 96, 96)
CALL = (214, 32, 32)


def annotate(canvas, title, items, sub=None, pad_left=20, pad_top=100, show_traces=True):
    cw, ch = canvas.size
    right_w = 480
    heights = [52 + len(l) * 34 for _, _, l in items]
    total = sum(heights) + 44 * (len(items) - 1)
    H = max(ch + pad_top + 120, pad_top + total + 170)
    W = pad_left + cw + right_w
    img = Image.new("RGB", (W, H), (250, 250, 251))
    d = ImageDraw.Draw(img)
    col = pad_left + cw + 20
    if show_traces:
        y = pad_top + 30
        for (num, (ax, ay), lines), h in zip(items, heights):
            d.line((col + 44, y + 22, ax + pad_left, ay + pad_top), fill=CALL, width=3)
            y += h + 44
    img.paste(canvas, (pad_left, pad_top))
    for (num, (ax, ay), lines) in items:
        d.ellipse((ax + pad_left - 8, ay + pad_top - 8, ax + pad_left + 8, ay + pad_top + 8), fill=CALL)
    T(d, (pad_left, 26), title, 30, True, (45, 45, 50))
    y = pad_top + 30
    for (num, (ax, ay), lines), h in zip(items, heights):
        cy = y + 22
        d.ellipse((col + 22, cy - 22, col + 66, cy + 22), fill=CALL)
        nf = F(24, True)
        tb = d.textbbox((0, 0), str(num), font=nf)
        d.text((col + 44 - (tb[2] - tb[0]) / 2, cy - (tb[3] - tb[1]) / 2 - tb[1]), str(num), font=nf, fill=(255, 255, 255))
        ty = cy + 36
        for ln in lines:
            T(d, (col + 2, ty), ln, 23, True, CALL)
            ty += 34
        y += h + 44
    if sub:
        T(d, (pad_left, H - 54), sub, 21, False, (135, 135, 140))
    return img


def desktop_bg(d, box, label="桌面 / 文件资源管理器"):
    x0, y0, x1, y1 = box
    R(d, (x0, y0, x1, y1), 14, fill=WIN_BG, outline=(222, 222, 222), width=2)
    T(d, (x0 + 20, y0 + 14), label, 21, False, (150, 150, 155))
    fx, fy = x0 + 36, y0 + 90
    d.rectangle((fx, fy, fx + 42, fy + 54), fill=(255, 255, 255), outline=(170, 175, 185), width=2)
    d.rectangle((fx + 6, fy - 10, fx + 24, fy + 2), fill=(255, 255, 255), outline=(170, 175, 185), width=2)
    R(d, (fx - 6, fy - 18, fx + 48, fy + 62), 6, outline=BLUE, width=3)
    T(d, (fx - 16, fy + 70), "选中的文件", 19, False, GREY)


def new_menu(d, ox, oy, w=380, mark_showmore=True, mark_icons=False):
    """绘制 Windows 11 新右键菜单，返回各行 y 坐标与总高。"""
    rows = ["打开", "在新选项卡中打开", "固定到\"快速访问\"", "压缩为 ZIP 文件"]
    h = 26 + len(rows) * 44 + 12 + 84 + 44 + 44 + 12 + 44 + 12 + 44 + 8
    R(d, (ox, oy, ox + w, oy + h), 12, fill=MENU_BG, outline=(214, 214, 214), width=2)
    pos = {}
    y = oy + 26
    for i, r in enumerate(rows):
        pos["row%d" % i] = (ox + w / 2, y + 14)
        T(d, (ox + 26, y), r, 23)
        y += 44
    d.line((ox + 18, y - 4, ox + w - 18, y - 4), fill=MENU_LINE, width=2)
    y += 10
    icons = ["剪切", "复制", "重命名", "共享", "删除"]
    step = (w - 36) / len(icons)
    if mark_icons:
        R(d, (ox + 6, y - 12, ox + w - 6, y + 76), 10, outline=CALL, width=4)
    for i, name in enumerate(icons):
        cx = ox + 18 + step * i + step / 2
        ic = (120, 120, 125)
        if name == "剪切":
            d.line((cx - 14, y + 22, cx + 4, y + 4), fill=ic, width=3)
            d.line((cx - 4, y + 26, cx + 14, y + 8), fill=ic, width=3)
        elif name == "复制":
            R(d, (cx - 14, y + 2, cx + 8, y + 24), 4, outline=ic, width=3)
            R(d, (cx - 6, y + 10, cx + 16, y + 32), 4, outline=ic, width=3)
        elif name == "重命名":
            d.line((cx - 14, y + 26, cx + 12, y), fill=ic, width=4)
        elif name == "共享":
            d.ellipse((cx - 16, y + 8, cx - 2, y + 22), fill=ic)
            d.ellipse((cx + 4, y, cx + 18, y + 14), fill=ic)
            d.ellipse((cx + 2, y + 20, cx + 16, y + 34), fill=ic)
        else:
            d.line((cx - 12, y + 6, cx + 12, y + 30), fill=ic, width=3)
            d.line((cx + 12, y + 6, cx - 12, y + 30), fill=ic, width=3)
        T(d, (cx - 22, y + 44), name, 20, False, GREY)
    pos["icons"] = (ox + w / 2, y + 30)
    y += 84
    pos["openwith"] = (ox + w / 2, y + 14)
    T(d, (ox + 26, y), "打开方式", 23)
    T(d, (ox + w - 40, y), ">", 22, False, GREY)
    y += 44
    pos["copypath"] = (ox + w / 2, y + 14)
    T(d, (ox + 26, y), "复制文件地址", 23)
    y += 44
    d.line((ox + 18, y - 4, ox + w - 18, y - 4), fill=MENU_LINE, width=2)
    y += 12
    pos["props"] = (ox + w / 2, y + 14)
    T(d, (ox + 26, y), "属性", 23)
    y += 44
    R(d, (ox + 8, y - 6, ox + w - 8, y + 34), 8, fill=SEL_BG)
    if mark_showmore:
        R(d, (ox + 6, y - 8, ox + w - 6, y + 36), 10, outline=CALL, width=4)
    pos["showmore"] = (ox + w / 2, y + 14)
    T(d, (ox + 26, y), "显示更多选项", 23, True)
    T(d, (ox + w - 40, y), ">", 22, False, GREY)
    return pos, h


def legacy_menu(d, ox, oy, w=360):
    items = [("打开", 0), ("在新窗口中打开", 0), ("添加到压缩文件…", 0),
             ("解压到当前文件夹", 0), ("使用 7-Zip 打开", 0), ("CRC SHA", 1),
             ("打开方式", 1), ("发送到", 1), ("剪切", 0), ("复制", 0),
             ("创建快捷方式", 0), ("删除", 0), ("重命名", 0), ("属性", 0)]
    h = 18 + len(items) * 38 + 16
    R(d, (ox, oy, ox + w, oy + h), 8, fill=(249, 249, 249), outline=(202, 202, 202), width=2)
    pos = []
    y = oy + 16
    for name, sub in items:
        if name in ("CRC SHA", "打开方式", "发送到"):
            d.line((ox + 8, y - 5, ox + w - 8, y - 5), fill=(228, 228, 228), width=2)
        pos.append((ox + w / 2, y + 12))
        T(d, (ox + 18, y), name, 21)
        if sub:
            T(d, (ox + w - 30, y), ">", 20, False, GREY)
        y += 38
    return pos, h


# ---------------- 图 3：新菜单本身 ----------------
def fig3():
    W, H = 800, 820
    img = Image.new("RGB", (W, H), (245, 245, 246))
    d = ImageDraw.Draw(img)
    desktop_bg(d, (20, 20, W - 40, H - 40))
    ox, oy, w = 300, 90, 380
    pos, h = new_menu(d, ox, oy, w, mark_showmore=True, mark_icons=True)
    items = [
        (1, pos["showmore"], ["使用者最需要的命令被折叠", "一次右键变成两步"]),
        (2, pos["icons"], ["只有图标没有文字", "剪切 / 复制 / 重命名靠猜"]),
        (3, (ox + w - 12, pos["copypath"][1]), ["层级被拉平：常用与罕见同权", "没有分组，扫视成本上升"]),
    ]
    return annotate(img, "图 3  Windows 11 文件资源管理器的新右键菜单（按公开界面重绘）", items,
                    "说明：菜单项名称与排列按 Windows 11 公开界面重绘，用于说明交互结构，非系统截图。",
                    pad_left=20, pad_top=90)


# ---------------- 图 4：两套菜单的割裂 ----------------
def fig4():
    W, H = 1460, 760
    img = Image.new("RGB", (W, H), (245, 245, 246))
    d = ImageDraw.Draw(img)

    # ① 新菜单 + 子菜单
    desktop_bg(d, (20, 20, 500, H - 40), "① 新菜单：常用项折叠，子菜单再展开")
    pos, h = new_menu(d, 60, 130, w=340, mark_showmore=False)
    sx, sy = 300, 330
    R(d, (sx, sy, sx + 250, sy + 16 + 5 * 38), 12, fill=MENU_BG, outline=(214, 214, 214), width=2)
    yy = sy + 12
    for name in ["照片", "画图", "记事本", "Windows 媒体播放器", "选择其他应用"]:
        T(d, (sx + 18, yy), name, 20)
        yy += 38

    # ② 旧菜单
    desktop_bg(d, (540, 20, 940, H - 40), "② 点「显示更多选项」后的旧菜单")
    lpos, lh = legacy_menu(d, 570, 80, w=340)
    T(d, (570, 80 + lh + 8), "压缩、CRC SHA、发送到全在这里", 19, False, (150, 150, 155))

    # ③ 结论
    desktop_bg(d, (980, 20, 1440, H - 40), "③ 问题所在")
    lines = ["同一动作 → 两套菜单", "", "新菜单看不到的命令，",
             "只能到旧菜单里找。", "", "命名、图标、分组、间距", "两套规则互不相同。", "", "结果："]
    yy = 110
    for ln in lines:
        T(d, (1010, yy), ln, 23, True if ln.endswith("：") else False, (70, 70, 75))
        yy += 36
    T(d, (1010, yy), "用户记不住「哪个在哪儿」，", 23, False, (70, 70, 75))
    T(d, (1010, yy + 36), "每次右键都在试。", 23, False, (70, 70, 75))

    items = [
        (1, (240, 210), ["新菜单只给 4 条 + 图标行", "其余命令全部折叠"]),
        (2, (740, 210), ["旧菜单的分组与命名", "与新菜单完全不一致"]),
        (3, (1120, 230), ["一次右键可能要走", "两层菜单 + 一次子菜单展开"]),
    ]
    return annotate(img, "图 4  「显示更多选项」把用户分到了两套完全不同的菜单里（示意图）", items,
                    "说明：按 Windows 11 / Windows 10 公开界面重绘，用于说明结构差异；非系统截图。",
                    pad_left=20, pad_top=90, show_traces=False)


# ---------------- 图 5：重新设计 ----------------
def fig5():
    W, H = 840, 860
    img = Image.new("RGB", (W, H), (245, 245, 246))
    d = ImageDraw.Draw(img)
    desktop_bg(d, (20, 20, W - 60, H - 40), "重新设计后（一屏一菜单）")

    ox, oy, w = 300, 100, 420
    rows = [("打开", "Enter"), ("在新选项卡中打开", ""), ("压缩为 ZIP 文件", "")]
    groups = [("编辑", [("剪切", "Ctrl+X"), ("复制", "Ctrl+C"), ("重命名", "F2"), ("删除", "Del")]),
              ("共享与发送", [("共享", ""), ("发送到", "")]),
              ("工具", [("使用 7-Zip 打开", ""), ("CRC SHA", ""), ("复制文件地址", "")])]
    total = len(rows) + sum(len(g[1]) + 1 for g in groups) + 1
    h = 24 + total * 40 + 24
    R(d, (ox, oy, ox + w, oy + h), 12, fill=MENU_BG, outline=(214, 214, 214), width=2)
    y = oy + 22
    a1 = None
    for name, key in rows:
        T(d, (ox + 24, y), name, 23, True)
        if key:
            T(d, (ox + w - 108, y + 3), key, 19, False, GREY)
        y += 40
    d.line((ox + 16, y - 6, ox + w - 16, y - 6), fill=MENU_LINE, width=2)
    y += 6
    a2 = None
    for gname, glist in groups:
        T(d, (ox + 24, y), gname, 20, True, (120, 120, 125))
        if a2 is None:
            a2 = (ox + 130, y + 10)
        y += 40
        for name, key in glist:
            T(d, (ox + 40, y), name, 22)
            if key:
                T(d, (ox + w - 110, y + 3), key, 19, False, GREY)
            y += 40
    d.line((ox + 16, y - 6, ox + w - 16, y - 6), fill=MENU_LINE, width=2)
    y += 6
    T(d, (ox + 24, y), "属性", 22)
    y += 40
    R(d, (ox + 10, y - 6, ox + w - 10, y + 34), 8, fill=SEL_BG)
    T(d, (ox + 24, y), "显示全部命令（经典菜单）", 22, True)
    T(d, (ox + w - 118, y + 3), "Shift+F10", 18, False, GREY)
    a3 = (ox + 210, y + 14)

    items = [
        (1, a1 if a1 else (ox + 200, oy + 30), ["常用命令不再折叠", "一次右键即可看到"]),
        (2, a2, ["按语义分组并写出组名", "扫视靠标题而不是记位置"]),
        (3, a3, ["折叠入口保留但改名", "并标出快捷键"]),
    ]
    return annotate(img, "图 5  重新设计方案：一屏一菜单、分组可见、快捷键可读（示意图）", items,
                    "说明：本图为本文提出的改造方案示意，非任何系统的真实界面。",
                    pad_left=20, pad_top=90)


if __name__ == "__main__":
    fig3().save(os.path.join(OUT, "fig3_win11_menu.png"))
    fig4().save(os.path.join(OUT, "fig4_win11_split.png"))
    fig5().save(os.path.join(OUT, "fig5_win11_redesign.png"))
    print("ok")
