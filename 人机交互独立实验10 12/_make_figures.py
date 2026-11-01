# -*- coding: utf-8 -*-
"""生成作业示意图（Pillow 绘制，非真实截图）。批注统一放在右侧编号栏。"""
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


def T(d, xy, text, size=22, bold=False, fill=(34, 34, 34)):
    d.text(xy, text, font=F(size, bold), fill=fill)


ALI_BLUE = (22, 119, 255)
JD_RED = (226, 35, 26)
GREY_LINE = (216, 216, 216)
TXT = (34, 34, 34)
TXT_GREY = (150, 150, 150)
CALL = (214, 32, 32)


def phone(W=720, H=1560):
    img = Image.new("RGB", (W, H), (250, 250, 251))
    d = ImageDraw.Draw(img)
    R(d, (20, 20, 660, H - 40), 46, fill=(255, 255, 255), outline=(190, 190, 195), width=3)
    T(d, (40, 44), "9:41", 26, True)
    for x in (500, 514, 528):
        d.rectangle((x, 46, x + 14, 64), fill=TXT)
    d.rectangle((580, 48, 634, 64), outline=TXT, width=3)
    d.rectangle((584, 52, 622, 60), fill=TXT)
    return img, d


def qr(d, box, n=21, seed=7):
    x0, y0, x1, y1 = box
    cell = (x1 - x0) / n
    rnd = seed
    for r in range(n):
        for c in range(n):
            rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
            on = (rnd >> 16) & 1
            if (r < 7 and c < 7) or (r < 7 and c >= n - 7) or (r >= n - 7 and c < 7):
                on = 0
            if on:
                d.rectangle((x0 + c * cell, y0 + r * cell, x0 + (c + 1) * cell, y0 + (r + 1) * cell), fill=(0, 0, 0))
    for (br, bc) in [(0, 0), (0, n - 7), (n - 7, 0)]:
        d.rectangle((x0 + bc * cell, y0 + br * cell, x0 + (bc + 7) * cell, y0 + (br + 7) * cell),
                    fill=(255, 255, 255), outline=(0, 0, 0), width=max(2, int(cell)))
        d.rectangle((x0 + (bc + 2) * cell, y0 + (br + 2) * cell, x0 + (bc + 5) * cell, y0 + (br + 5) * cell),
                    fill=(0, 0, 0))


def barcode(d, box, seed=3):
    x0, y0, x1, y1 = box
    x = x0
    rnd = seed
    while x < x1 - 2:
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        w = 2 + (rnd >> 18) % 5
        if (rnd >> 8) & 1:
            d.rectangle((x, y0, min(x + w, x1), y1), fill=(0, 0, 0))
        x += w + 2 + (rnd >> 12) % 3


def check(d, cx, cy, r=40, color=(46, 178, 96)):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    d.line((cx - r * 0.42, cy + r * 0.02, cx - r * 0.1, cy + r * 0.38), fill=(255, 255, 255), width=8)
    d.line((cx - r * 0.1, cy + r * 0.38, cx + r * 0.46, cy - r * 0.34), fill=(255, 255, 255), width=8)


def annotate(canvas, title, items, sub=None, pad_left=20, pad_top=100):
    cw, ch = canvas.size
    right_w = 480
    heights = [52 + len(l) * 34 for _, _, l in items]
    total = sum(heights) + 44 * (len(items) - 1)
    H = max(ch + pad_top + 120, pad_top + total + 170)
    W = pad_left + cw + right_w
    img = Image.new("RGB", (W, H), (250, 250, 251))
    d = ImageDraw.Draw(img)
    col = pad_left + cw + 20
    y = pad_top + 30
    # 先把连线画在底层，再把界面贴到上层，线在界面边缘自然截断，避免压住按钮文字
    for (num, (ax, ay), lines), h in zip(items, heights):
        cy = y + 22
        d.line((col + 44, cy, ax + pad_left, ay + pad_top), fill=CALL, width=3)
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


# ---------------- 图 1：支付宝付款码 ----------------
def fig1():
    img, d = phone()
    # 先画顶部蓝条，再画白色卡片，使卡片圆角正确覆盖蓝条下缘
    d.rectangle((20, 86, 660, 250), fill=ALI_BLUE)
    tb = d.textbbox((0, 0), "付款码", font=F(34, True))
    d.text((340 - (tb[2] - tb[0]) / 2, 104), "付款码", font=F(34, True), fill=(255, 255, 255))
    T(d, (48, 116), "<", 38, True, (255, 255, 255))
    T(d, (610, 116), "···", 30, True, (255, 255, 255))
    R(d, (66, 196, 614, 700), 26, fill=(255, 255, 255))
    T(d, (90, 226), "付款码", 26, True)
    d.rectangle((66, 276, 614, 278), fill=GREY_LINE)
    barcode(d, (100, 320, 580, 430))
    T(d, (232, 452), "2 8 6 4  9 1 7 3  5 0 2 8", 26)
    T(d, (232, 500), "数字为脱敏编号（示意）", 19, False, TXT_GREY)
    qr(d, (235, 528, 445, 690), n=25, seed=11)
    R(d, (66, 726, 614, 812), 20, fill=(248, 249, 251))
    d.ellipse((96, 750, 144, 798), fill=ALI_BLUE)
    T(d, (111, 757), "A", 26, True, (255, 255, 255))
    T(d, (164, 746), "当前付款方式", 22, False, TXT_GREY)
    T(d, (164, 774), "余额宝  >", 26, True)
    T(d, (500, 760), "更换", 24, False, ALI_BLUE)
    T(d, (66, 838), "付款码仅用于线下付款，请勿转发他人", 21, False, TXT_GREY)
    T(d, (232, 900), "（同一屏幕不再放广告位）", 20, False, (185, 185, 190))

    items = [
        (1, (340, 372), ["单一任务占满整屏", "收银台前零寻找成本"]),
        (2, (340, 486), ["一维码与二维码同屏", "两类扫码枪都能读"]),
        (3, (580, 772), ["付款方式就在同一屏", "可直接更换，不必返回"]),
    ]
    return annotate(img, "图 1  支付宝「付款码」主界面（示意图，非真实截图）", items,
                    "说明：界面为按公开资料重绘的示意图，用于说明设计特征，不代表支付宝当下真实版本。")


# ---------------- 图 2：支付宝三步流程 ----------------
def fig2():
    W, H = 1400, 1010
    img = Image.new("RGB", (W, H), (250, 250, 251))
    d = ImageDraw.Draw(img)

    def mini(ox, oy, title):
        R(d, (ox, oy, ox + 380, oy + 700), 30, fill=(255, 255, 255), outline=(190, 190, 195), width=3)
        T(d, (ox + 26, oy + 22), title, 24, True, (80, 80, 80))
        d.rectangle((ox + 24, oy + 62, ox + 356, oy + 64), fill=GREY_LINE)

    ox, oy = 60, 110
    mini(ox, oy, "① 首页：入口直给")
    d.rectangle((ox + 24, oy + 78, ox + 356, oy + 330), fill=(238, 244, 255))
    T(d, (ox + 40, oy + 92), "搜索 / 最近使用", 22, False, (120, 140, 180))
    for i, (label, color) in enumerate([("扫一扫", ALI_BLUE), ("收付款", ALI_BLUE),
                                        ("出行", (255, 152, 0)), ("卡包", (120, 120, 120))]):
        cx = ox + 74 + (i % 2) * 170
        cy = oy + 140 + (i // 2) * 96
        d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), fill=color)
        T(d, (cx - 26, cy + 34), label, 22, True)
    d.rectangle((ox + 24, oy + 360, ox + 356, oy + 680), fill=(250, 250, 251))
    T(d, (ox + 40, oy + 380), "（其余为服务与内容区）", 20, False, TXT_GREY)

    ox2 = 510
    mini(ox2, oy, "② 付款码：一屏一任务")
    d.rectangle((ox2 + 24, oy + 78, ox2 + 356, oy + 170), fill=ALI_BLUE)
    T(d, (ox2 + 40, oy + 96), "付款码", 26, True, (255, 255, 255))
    R(d, (ox2 + 44, oy + 190, ox2 + 336, oy + 520), 18, fill=(255, 255, 255), outline=GREY_LINE)
    barcode(d, (ox2 + 66, oy + 226, ox2 + 314, oy + 300))
    T(d, (ox2 + 92, oy + 316), "2864 9173 5028", 19)
    qr(d, (ox2 + 150, oy + 360, ox2 + 268, oy + 478), n=21, seed=5)
    T(d, (ox2 + 44, oy + 546), "支付方式：余额宝 >", 21)
    T(d, (ox2 + 44, oy + 592), "亮度自动最高（示意）", 20, False, TXT_GREY)

    ox3 = 960
    mini(ox3, oy, "③ 结果：毫秒级反馈")
    check(d, ox3 + 190, oy + 200)
    T(d, (ox3 + 116, oy + 262), "支付成功", 30, True)
    T(d, (ox3 + 118, oy + 312), "¥ 18.50", 40, True)
    T(d, (ox3 + 60, oy + 392), "语音播报：支付宝到账 18.5 元", 20, False, TXT_GREY)
    T(d, (ox3 + 60, oy + 424), "用户与收银员同时获得确认", 20, False, TXT_GREY)

    for i in range(2):
        x0 = 60 + 450 * (i + 1) - 34
        d.polygon([(x0, 420), (x0 + 26, 450), (x0, 480)], fill=(170, 170, 175))

    items = [
        (1, (134, 250), ["首页首屏直接给入口", "不必进二级菜单"]),
        (2, (ox2 + 100, oy + 610), ["亮度、防截屏等保护", "由系统默认完成"]),
        (3, (ox3 + 190, oy + 180), ["反馈同时到达协作双方", "消除「他没扫上」的尴尬"]),
    ]
    return annotate(img, "图 2  从首页到支付完成：三步、三次可见（示意图）", items,
                    "说明：流程按公开资料重绘；实际界面随版本变化。", pad_left=20, pad_top=110)


# ---------------- 图 3：京东订单列表 ----------------
def fig3():
    img, d = phone()
    T(d, (48, 106), "<", 34, True)
    T(d, (276, 110), "我的订单", 32, True)
    for i, t in enumerate(["全部", "待付款", "待发货", "待收货", "待评价"]):
        x = 52 + i * 116
        T(d, (x, 156), t, 23, True if i == 0 else False, JD_RED if i == 0 else (110, 110, 110))
    d.rectangle((52, 194, 98, 198), fill=JD_RED)

    R(d, (40, 224, 640, 480), 18, fill=(255, 255, 255), outline=GREY_LINE)
    T(d, (64, 244), "京东自营 · 已下单", 22, False, TXT_GREY)
    T(d, (536, 244), "等待发货", 23, True, JD_RED)
    R(d, (64, 288, 196, 420), 12, fill=(238, 240, 244))
    T(d, (88, 340), "商品图", 22, False, (160, 165, 175))
    T(d, (218, 292), "无线蓝牙耳机（示例商品）", 25, True)
    T(d, (218, 330), "颜色：白色 / 数量：1", 21, False, TXT_GREY)
    T(d, (218, 380), "¥ 299.00", 28, True)
    d.rectangle((40, 432, 640, 434), fill=GREY_LINE)
    R(d, (432, 444, 620, 472), 14, outline=(190, 190, 195), width=2)
    T(d, (470, 448), "取消订单", 21, False, (90, 90, 90))

    R(d, (40, 510, 640, 710), 18, fill=(255, 255, 255), outline=GREY_LINE)
    T(d, (64, 530), "京东自营 · 已发货", 22, False, TXT_GREY)
    T(d, (566, 530), "运输中", 23, True, (46, 140, 90))
    R(d, (64, 572, 196, 686), 12, fill=(238, 240, 244))
    T(d, (88, 620), "商品图", 22, False, (160, 165, 175))
    T(d, (218, 576), "抽纸 3 层 100 抽（示例）", 25, True)
    T(d, (218, 614), "已发货，无法直接取消", 21, False, TXT_GREY)
    R(d, (446, 648, 620, 680), 16, outline=(190, 190, 195), width=2)
    T(d, (468, 654), "申请售后", 21, False, (90, 90, 90))

    T(d, (40, 744), "上滑查看更多订单", 22, False, TXT_GREY)
    T(d, (40, 820), "同一动作的名称随状态变化：", 22, True, (120, 120, 125))
    T(d, (40, 854), "取消订单 / 申请售后 / 申请退款", 22, False, (120, 120, 125))

    items = [
        (1, (526, 458), ["目标是「取消」", "按钮最小、灰色、最靠右"]),
        (2, (530, 664), ["已发货后同一动作改名", "用户必须重新寻找"]),
        (3, (300, 748), ["列表里取消入口不稳定", "左滑是否可用随版本变化"]),
    ]
    return annotate(img, "图 3  京东订单列表：「取消订单」的位置与命名（示意图）", items,
                    "说明：界面按公开投诉记录与常见流程重绘，用于说明设计特征，非实时截图。")


# ---------------- 图 4：挽留三层 ----------------
def fig4():
    W, H = 1400, 1080
    img = Image.new("RGB", (W, H), (250, 250, 251))
    d = ImageDraw.Draw(img)
    PW = 380

    def mini(ox, oy, label, tone):
        R(d, (ox, oy, ox + PW, oy + 860), 30, fill=(255, 255, 255), outline=(190, 190, 195), width=3)
        R(d, (ox + 22, oy + 24, ox + PW - 22, oy + 76), 14, fill=tone)
        T(d, (ox + 36, oy + 34), label, 22, True, (255, 255, 255))

    x1, x2, x3, oy = 30, 450, 870, 100

    mini(x1, oy, "第 1 层  选择取消原因", (120, 120, 125))
    T(d, (x1 + 36, oy + 100), "请选择取消原因", 26, True)
    for i, r in enumerate(["不想要了", "信息填写错误", "重复下单", "其他渠道更便宜", "其他原因"]):
        y = oy + 160 + i * 74
        d.ellipse((x1 + 40, y + 6, x1 + 64, y + 30), outline=(180, 180, 185), width=3)
        T(d, (x1 + 82, y), r, 23)
    R(d, (x1 + 40, oy + 560, x1 + PW - 40, oy + 620), 18, fill=JD_RED)
    T(d, (x1 + 156, oy + 574), "下一步", 25, True, (255, 255, 255))

    mini(x2, oy, "第 2 层  挽留 + 倒计时", (200, 90, 20))
    T(d, (x2 + 36, oy + 100), "订单取消后将无法恢复", 24, True)
    R(d, (x2 + 40, oy + 152, x2 + PW - 40, oy + 350), 16, fill=(255, 246, 236), outline=(245, 190, 140), width=3)
    T(d, (x2 + 64, oy + 176), "为您保留订单，可享：", 22, False, (180, 90, 20))
    T(d, (x2 + 64, oy + 220), "满 199 减 30 优惠券", 27, True, (220, 90, 20))
    T(d, (x2 + 64, oy + 274), "仅剩 04:59 有效", 25, True, CALL)
    R(d, (x2 + 40, oy + 390, x2 + PW - 40, oy + 452), 22, fill=JD_RED)
    T(d, (x2 + 158, oy + 405), "再想想", 27, True, (255, 255, 255))
    R(d, (x2 + 40, oy + 474, x2 + PW - 40, oy + 536), 22, fill=(255, 255, 255), outline=(200, 200, 205), width=2)
    T(d, (x2 + 134, oy + 490), "狠心取消", 25, False, (130, 130, 135))

    mini(x3, oy, "第 3 层  二次确认", (120, 120, 125))
    T(d, (x3 + 36, oy + 100), "确认取消订单？", 26, True)
    T(d, (x3 + 36, oy + 152), "取消后优惠券将退回，", 22, False, TXT_GREY)
    T(d, (x3 + 36, oy + 186), "款项 1–3 个工作日退回", 22, False, TXT_GREY)
    R(d, (x3 + 40, oy + 266, x3 + PW - 40, oy + 330), 22, fill=(255, 255, 255), outline=(200, 200, 205), width=2)
    T(d, (x3 + 142, oy + 282), "再考虑一下", 24, False, (130, 130, 135))
    R(d, (x3 + 40, oy + 352, x3 + PW - 40, oy + 416), 22, fill=JD_RED)
    T(d, (x3 + 146, oy + 368), "确认取消", 26, True, (255, 255, 255))

    items = [
        (1, (x1 + 190, oy + 590), ["只想取消，先做选择题", "把目标降级成流程必填项"]),
        (2, (x2 + 190, oy + 300), ["倒计时制造失复焦虑", "用紧迫感替代说服"]),
        (3, (x2 + PW - 40, oy + 420), ["主色按钮是「再想想」", "取消被降级成灰按钮"]),
        (4, (x3 + PW - 40, oy + 384), ["第 3 次点击才到达目标", "系统并不缩短路径"]),
    ]
    return annotate(img, "图 4  一次点击之后：连续三层打断（示意图）", items,
                    "说明：按公开投诉记录与常见流程重绘。用户目标为 1 次点击，实际路径为 3 层弹窗 + 原因选择。",
                    pad_left=20, pad_top=90)


# ---------------- 图 5：改造后 ----------------
def fig5():
    W, H = 1400, 1020
    img = Image.new("RGB", (W, H), (250, 250, 251))
    d = ImageDraw.Draw(img)
    PW = 380

    def frame(ox, label):
        R(d, (ox, 100, ox + PW, 780), 30, fill=(255, 255, 255), outline=(190, 190, 195), width=3)
        T(d, (ox + 28, 122), label, 22, True, (80, 80, 80))
        d.rectangle((ox + 24, 160, ox + PW - 24, 162), fill=GREY_LINE)

    x1, x2, x3 = 30, 450, 870
    frame(x1, "订单列表：动作常驻、命名统一")
    for i, (st, name) in enumerate([("等待发货", "取消订单"), ("运输中", "申请售后")]):
        y = 186 + i * 190
        R(d, (x1 + 26, y, x1 + PW - 26, y + 160), 14, fill=(252, 252, 253), outline=GREY_LINE)
        T(d, (x1 + 44, y + 16), name + " · " + st, 21, True)
        R(d, (x1 + 44, y + 56, x1 + 116, y + 124), 10, fill=(238, 240, 244))
        T(d, (x1 + 176, y + 124), "¥ 299.00", 23, True)
        R(d, (x1 + 176, y + 12, x1 + PW - 40, y + 52), 18, fill=JD_RED)
        T(d, (x1 + 204, y + 19), name, 22, True, (255, 255, 255))
    T(d, (x1 + 36, 584), "负向动作 = 一等公民", 23, True, (46, 140, 90))
    T(d, (x1 + 36, 624), "全站唯一名称：取消订单", 22, False, TXT_GREY)
    T(d, (x1 + 36, 658), "（售后 / 退款另立名称，不混用）", 21, False, TXT_GREY)
    T(d, (x1 + 36, 700), "入口稳定：列表卡片 + 详情页", 22, False, TXT_GREY)

    frame(x2, "底部抽屉：确认 + 挽留同屏")
    T(d, (x2 + 36, 186), "取消订单", 26, True)
    T(d, (x2 + 36, 230), "取消原因（可不填）", 22, False, TXT_GREY)
    T(d, (x2 + 36, 266), "款项 1–3 个工作日退回原路", 22, False, TXT_GREY)
    R(d, (x2 + 32, 312, x2 + PW - 32, 542), 16, fill=(255, 249, 240), outline=(245, 200, 150), width=3)
    T(d, (x2 + 52, 330), "可选：保留订单可享", 22, False, (180, 100, 30))
    T(d, (x2 + 52, 368), "满 199 减 30", 30, True, (210, 110, 30))
    T(d, (x2 + 52, 420), "无倒计时、无「最后机会」", 21, False, (185, 140, 90))
    R(d, (x2 + 52, 462, x2 + PW - 52, 518), 24, fill=(255, 255, 255), outline=(230, 170, 110), width=2)
    T(d, (x2 + 126, 476), "保留订单并使用", 23, True, (210, 110, 30))
    R(d, (x2 + 32, 572, x2 + PW - 32, 642), 30, fill=JD_RED)
    T(d, (x2 + 138, 590), "确认取消", 27, True, (255, 255, 255))
    T(d, (x2 + 100, 664), "主按钮 = 用户的目标", 21, False, TXT_GREY)
    T(d, (x2 + 36, 700), "一次点击进入，一次确认结束", 22, False, TXT_GREY)

    frame(x3, "取消后：状态可见、可导出")
    T(d, (x3 + 36, 186), "订单已取消", 28, True, (46, 140, 90))
    for i, t in enumerate(["退款 ¥299.00 预计 10-14 到账", "优惠券已退回账户（有效期不变）",
                           "查看取消记录", "下载本次订单凭证"]):
        y = 236 + i * 64
        R(d, (x3 + 32, y, x3 + PW - 32, y + 52), 12, fill=(250, 250, 251), outline=GREY_LINE)
        T(d, (x3 + 50, y + 14), t, 21)
    T(d, (x3 + 36, 516), "负向结果同样给确定信息", 22, True, (46, 140, 90))
    T(d, (x3 + 36, 554), "不留悬空状态，不做数据绑架", 21, False, TXT_GREY)
    T(d, (x3 + 36, 596), "线下 7 天内可恢复订单（可选）", 22, False, TXT_GREY)

    items = [
        (1, (x1 + PW - 40, 208), ["负向动作常驻可见", "不必进「更多」菜单"]),
        (2, (x2 + PW - 32, 606), ["取消是主按钮", "挽留降级为可选卡片"]),
        (3, (x3 + PW - 32, 262), ["把「可能失去」", "改成「会归还」"]),
    ]
    return annotate(img, "图 5  重新设计方案：一次点击、一次确认、同屏挽留（示意图）", items,
                    "说明：本图为本文提出的改造方案示意，非任何产品的真实界面。", pad_left=20, pad_top=90)


if __name__ == "__main__":
    fig1().save(os.path.join(OUT, "fig1_alipay_paycode.png"))
    fig2().save(os.path.join(OUT, "fig2_alipay_flow.png"))
    fig3().save(os.path.join(OUT, "fig3_jd_cancel_entry.png"))
    fig4().save(os.path.join(OUT, "fig4_jd_retention.png"))
    fig5().save(os.path.join(OUT, "fig5_redesign.png"))
    print("ok")
