"""Эпизод «Один организм под лесом» — грибница опёнка в Орегоне.

Формат cartoon_engine, 9:16. Живая сеть мицелия растёт под землёй,
по нитям движутся частицы питательных веществ, деревья обмениваются.
"""
import math
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cartoon_engine import FFMPEG, S, W, H, FPS, ease, label, leader, lerp, synthesize, audio_duration, font_path
from cartoon_mariana import draw_caption, phrase_cues

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "storage", "cartoon-mycelium")
F_LABEL = ImageFont.truetype(font_path(), S(30))
F_TICK = ImageFont.truetype(font_path(), S(23))
F_BIG = ImageFont.truetype(font_path(), S(52))

TEXT = ("Под этим лесом лежит один живой организм. "
        "Грибница опёнка в Орегоне занимает почти десять квадратных километров: "
        "это больше тысячи футбольных полей, и всё это один геном. "
        "Возраст — около двух с половиной тысяч лет. "
        "Грибы, которые мы видим, — только плодовые тела: над землёй показывается доля процента, "
        "остальное скрыто в почве. "
        "По этим нитям деревья обмениваются водой и сахаром: взрослые подкармливают молодые побеги. "
        "Один лес — одна сеть.")

GROUND = 596
SKY_TOP, SKY_BOT = (250, 226, 196), (208, 232, 214)
SOIL_TOP, SOIL_BOT = (122, 88, 62), (58, 40, 32)


def build_network(seed=7):
    """Детерминированная сеть: узлы (x, y, parent, depth, birth)."""
    rnd = random.Random(seed)
    nodes = [(360.0, 1010.0, -1, 0, 0.0)]
    queue = [0]
    i = 1
    while queue:
        pi = queue.pop(0)
        px, py, _, depth, birth = nodes[pi]
        if depth >= 5:
            continue
        count = 3 if depth < 2 else 2
        for k in range(count):
            ang = -math.pi / 2 + (k - (count - 1) / 2) * 0.9 + rnd.uniform(-0.35, 0.35)
            if depth >= 2:
                ang += rnd.choice((-1, 1)) * rnd.uniform(0.5, 1.1)
            length = (188 if depth == 0 else 148) * rnd.uniform(0.66, 1.0) * (0.84 ** depth)
            nx = max(16.0, min(W - 16.0, px + math.cos(ang) * length))
            ny = max(GROUND + 40, min(1250.0, py + math.sin(ang) * length * 0.75))
            nodes.append((nx, ny, pi, depth + 1, birth + rnd.uniform(0.55, 1.2)))
            queue.append(i)
            i += 1
    # нормируем «время рождения» к 0..1
    mx = max(n[4] for n in nodes) or 1.0
    return [(n[0], n[1], n[2], n[3], n[4] / mx) for n in nodes]


NET = build_network()
# пути от листьев к корню — для частиц питательных веществ
LEAVES = [i for i, n in enumerate(NET) if n[3] >= 3]


def path_to_root(i):
    path = []
    while i > 0:
        path.append((NET[i][0], NET[i][1]))
        i = NET[i][2]
    path.append((NET[0][0], NET[0][1]))
    return path[::-1]


PATHS = [path_to_root(LEAVES[k % len(LEAVES)]) for k in range(6)]


def hypha(d, p0, p1, col, alpha, width, wig=3.4, seg=7):
    """Волнистая нить: прямая с поперечным синусом, читается как гифа."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1.0
    nxv, nyv = -dy / ln, dx / ln
    pts = []
    for i in range(seg + 1):
        k = i / seg
        off = math.sin(k * math.pi * 2.2) * wig * (1 - abs(k - 0.5)) * 1.6
        pts.append((S(x0 + dx * k + nxv * off), S(y0 + dy * k + nyv * off)))
    d.line(pts, fill=(*col, alpha), width=S(width), joint="curve")


def tree(d, x, base_y, scale, canopy, trunk=(96, 66, 48), sway=0.0):
    top = base_y - 300 * scale
    d.rectangle([S(x - 13 * scale), S(top), S(x + 13 * scale), S(base_y)], fill=trunk)
    for i in range(3):
        yy = top + i * 46 * scale
        d.line([(S(x), S(yy + 30 * scale)), (S(x), S(yy + 64 * scale))], fill=trunk, width=S(9 * scale))
    d.ellipse([S(x - 96 * scale), S(top - 78 * scale), S(x + 96 * scale), S(top + 74 * scale)],
              fill=canopy)
    d.ellipse([S(x - 128 * scale + sway), S(top - 20 * scale), S(x + 30 * scale + sway), S(top + 92 * scale)],
              fill=lerp(canopy, (255, 255, 255), 0.12))
    d.ellipse([S(x - 20 * scale - sway), S(top - 40 * scale), S(x + 126 * scale - sway), S(top + 70 * scale)],
              fill=lerp(canopy, (0, 0, 0), 0.10))
    # корни
    for k in (-1, 1):
        d.line([(S(x + k * 10 * scale), S(base_y - 8)), (S(x + k * 62 * scale), S(base_y + 46 * scale))],
               fill=trunk, width=S(12 * scale))


def mushroom(d, x, y, s, cap=(226, 138, 96), stem=(244, 232, 214)):
    d.rounded_rectangle([S(x - 7 * s), S(y - 34 * s), S(x + 7 * s), S(y)], radius=S(6 * s), fill=stem)
    d.pieslice([S(x - 30 * s), S(y - 62 * s), S(x + 30 * s), S(y - 16 * s)], 180, 360, fill=cap)
    d.pieslice([S(x - 30 * s), S(y - 60 * s), S(x + 30 * s), S(y - 30 * s)], 180, 360,
               fill=lerp(cap, (255, 255, 255), 0.22))
    for k in (-14, 0, 16):
        d.ellipse([S(x + k * s - 3 * s), S(y - 52 * s), S(x + k * s + 3 * s), S(y - 46 * s)],
                  fill=(246, 226, 206))


def root_system(d, x, base_y, s, t, link, seed=0):
    """Корни дерева + гифы, оплетающие кончики (микориза)."""
    rnd = random.Random(seed)
    tips = []
    for k, ang in enumerate((-0.55, -0.15, 0.25, 0.7)):
        ln = (150 + rnd.uniform(-24, 34)) * s
        ex = x + math.sin(ang) * ln * 0.65
        ey = base_y + math.cos(ang) * ln
        mx = (x + ex) / 2 + math.sin(ang) * 18
        my = (base_y + ey) / 2
        d.line([(S(x), S(base_y)), (S(mx), S(my))], fill=(122, 88, 64), width=S(9 * s))
        d.line([(S(mx), S(my)), (S(ex), S(ey))], fill=(136, 98, 72), width=S(6 * s))
        tips.append((ex, ey))
        for j in (-1, 1):
            bx = mx + j * 26 * s
            by = my + 26 * s
            d.line([(S(mx), S(my)), (S(bx), S(by))], fill=(128, 92, 68), width=S(4 * s))
            tips.append((bx, by))
    # гифы обвивают кончики
    if link > 0.05:
        for i, (tx, ty) in enumerate(tips):
            for k in range(3):
                rr = (14 + k * 9) * s
                d.arc([S(tx - rr), S(ty - rr * 0.7), S(tx + rr), S(ty + rr * 0.7)],
                      200 + k * 12, 340 + k * 12, fill=(214, 248, 222, int(210 * link)),
                      width=S(3))
            d.ellipse([S(tx - 6), S(ty - 6), S(tx + 6), S(ty + 6)],
                      fill=(255, 236, 176, int(230 * link)))
            # тонкая нить вниз, к сети
            d.line([(S(tx), S(ty)), (S(tx + math.sin(t * 0.7 + i) * 10), S(ty + 54 * s))],
                   fill=(198, 244, 220, int(170 * link)), width=S(2))


def draw_frame(d, t, total, text):
    p = min(1.0, t / max(0.1, total * 0.92))
    # небо
    for yy in range(0, S(GROUND)):
        d.line([(0, yy), (S(W), yy)], fill=lerp(SKY_TOP, SKY_BOT, yy / S(GROUND)))
    sun_x, sun_y = 588, 150
    glow = 1.0
    for r, a in ((96, 40), (70, 70), (48, 120)):
        d.ellipse([S(sun_x - r), S(sun_y - r), S(sun_x + r), S(sun_y + r)],
                  fill=(255, 224, 168, int(a * glow * 0.6)))
    d.ellipse([S(sun_x - 38), S(sun_y - 38), S(sun_x + 38), S(sun_y + 38)], fill=(255, 236, 186))
    # дальний ряд деревьев (дымка)
    for i, (tx, sc, col) in enumerate(((70, 0.42, (150, 190, 156)), (210, 0.36, (160, 198, 164)),
                                       (520, 0.40, (146, 188, 152)), (650, 0.33, (158, 196, 164)))):
        tree(d, tx, GROUND - 6, sc, col, trunk=(140, 130, 112))
    # почва
    for yy in range(S(GROUND), S(H)):
        k = (yy - S(GROUND)) / max(1, S(H) - S(GROUND))
        d.line([(0, yy), (S(W), yy)], fill=lerp(SOIL_TOP, SOIL_BOT, k ** 0.8))
    d.rectangle([0, S(GROUND), S(W), S(GROUND + 6)], fill=(92, 128, 74))
    # камешки
    for i in range(16):
        cx = (i * 137 + 41) % W
        cy = GROUND + 60 + ((i * 211) % 560)
        r = 8 + (i % 4) * 4
        d.ellipse([S(cx - r), S(cy - r * 0.62), S(cx + r), S(cy + r * 0.62)],
                  fill=lerp((132, 106, 84), (88, 68, 54), (i % 5) / 5))
    # корни крупных деревьев
    for tx, sc, col in ((150, 0.95, (104, 176, 118)), (360, 1.05, (86, 160, 108)), (588, 0.88, (120, 188, 126))):
        tree(d, tx, GROUND + 2, sc, col, sway=math.sin(t * 0.8 + tx) * 4)
    # сеть мицелия: рост по времени
    grow = ease(min(1.0, (t - total * 0.06) / (total * 0.55)))
    for i, (nx, ny, parent, depth, birth) in enumerate(NET):
        if parent < 0 or birth > grow:
            continue
        px, py = NET[parent][0], NET[parent][1]
        k = depth / 5.0
        col = lerp((132, 240, 206), (92, 172, 244), k)
        alpha = int(135 + 85 * (1 - k))
        hypha(d, (px, py), (nx, ny), col, alpha, max(2, 10 - depth * 1.7), wig=2.2 + depth * 0.7)
        if depth >= 3:
            d.ellipse([S(nx - 5), S(ny - 5), S(nx + 5), S(ny + 5)], fill=(*col, 225))
    # корни с микоризой (рисуем до сети, чтобы гифы легли поверх)
    for i, (tx, sc) in enumerate(((150, 0.95), (360, 1.05), (588, 0.88))):
        root_system(d, tx, GROUND + 10, sc, t, ease(min(1.0, (t - total * 0.30) / (total * 0.30))), seed=i * 5)

    # связи «дерево — сеть» и «гриб — сеть»
    if grow > 0.25:
        link = ease(min(1.0, (grow - 0.25) / 0.5))
        for tx, nb in ((150, 26), (360, 0), (588, 49)):
            if nb >= len(NET):
                continue
            node = NET[nb]
            for k in (-1, 0, 1):
                end = (node[0] + k * 16, node[1] + 12)
                start = (tx + k * 26, GROUND + 44)
                mx = (start[0] + end[0]) / 2 + k * 22
                my = (start[1] + end[1]) / 2
                hypha(d, start, (mx, my), (196, 240, 214), int(190 * link), 5, wig=5.0)
                hypha(d, (mx, my), end, (196, 240, 214), int(190 * link), 5, wig=5.0)
        for mx in (250, 300, 470):
            hypha(d, (mx, GROUND + 2), (NET[0][0] + (mx - 360) * 0.35, NET[0][1] - 120),
                  (236, 214, 180), int(150 * link), 3, wig=6.0)

    # частицы по нитям
    if t > total * 0.45:
        q = (t - total * 0.45) / (total * 0.55)
        for k, path in enumerate(PATHS):
            if len(path) < 2:
                continue
            head = ((q * 1.25 + k * 0.17) % 1.0) * (len(path) - 1)
            idx = int(head)
            frac = head - idx
            x0, y0 = path[idx]
            x1, y1 = path[min(len(path) - 1, idx + 1)]
            px, py = x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac
            col = (255, 214, 140) if k % 2 else (186, 232, 255)
            for rr, aa in ((17, 45), (11, 90), (6, 220)):
                d.ellipse([S(px - rr), S(py - rr), S(px + rr), S(py + rr)], fill=(*col, aa))
    # грибы над землёй
    if t > total * 0.28:
        mushroom(d, 250, GROUND - 2, 1.0)
        mushroom(d, 300, GROUND + 4, 0.72)
        mushroom(d, 470, GROUND, 0.85)
    # плашки
    if t > total * 0.18:
        d.rounded_rectangle([S(40), S(84), S(348), S(252)], radius=S(16),
                            fill=(26, 34, 44, 205), outline=(180, 232, 210, 130), width=S(2))
        d.text((S(58), S(96)), "9,6 км²", font=F_BIG, fill=(255, 226, 158))
        if t > total * 0.30:
            d.text((S(58), S(158)), "≈ 2 400 лет", font=F_LABEL, fill=(246, 240, 226))
        if t > total * 0.46:
            d.text((S(58), S(200)), "один геном", font=F_LABEL, fill=(188, 232, 255))
    # врезка «плодовые тела — верхушка»
    if t > total * 0.44:
        ix, iy, iw, ih = 404, 872, 282, 210
        d.rounded_rectangle([S(ix), S(iy), S(ix + iw), S(iy + ih)], radius=S(16),
                            fill=(24, 32, 42, 228), outline=(160, 220, 190, 190), width=S(3))
        d.text((S(ix + 14), S(iy + 10)), "плодовые тела", font=F_TICK, fill=(186, 236, 206))
        for i, (mx, ms) in enumerate(((ix + 58, 1.05), (ix + 132, 0.8), (ix + 196, 0.95))):
            mushroom(d, mx, iy + 150, ms)
        d.text((S(ix + 14), S(iy + ih - 34)), "это < 1 % грибницы", font=F_LABEL, fill=(255, 214, 150))
        leader(d, ix + 12, iy + 54, 474, GROUND + 10, colour=(186, 236, 206), alpha=200)
    # молодой побег и путь питания к нему
    sx, sy = 636, GROUND + 4
    d.line([(S(sx), S(sy)), (S(sx), S(sy - 56))], fill=(112, 158, 96), width=S(7))
    for k, ang in ((-0.9, -0.7), (0.9, -0.7), (-1.4, -0.2), (1.4, -0.2)):
        d.ellipse([S(sx + math.sin(ang) * 26 - 17), S(sy - 60 + math.cos(ang) * 16 - 10),
                   S(sx + math.sin(ang) * 26 + 17), S(sy - 60 + math.cos(ang) * 16 + 10)],
                  fill=(132, 196, 112))
    d.ellipse([S(sx - 13), S(sy - 84), S(sx + 13), S(sy - 58)], fill=(150, 210, 126))
    if t > total * 0.62:
        flow = ((t - total * 0.62) / (total * 0.38)) % 1.0
        hx, hy = NET[0][0], NET[0][1]
        for i in range(10):
            k = (flow + i * 0.1) % 1.0
            px = hx + (sx - hx) * k + math.sin(k * 6) * 10
            py = hy + (sy - 18 - hy) * k
            d.ellipse([S(px - 5), S(py - 5), S(px + 5), S(py + 5)], fill=(255, 232, 168, 210))
        d.text((S(sx - 62), S(sy - 128)), "побег", font=F_TICK, fill=(226, 244, 226),
               stroke_width=S(3), stroke_fill=(30, 44, 34))
    draw_caption(d, text, y=1148)


def main():
    os.makedirs(OUT, exist_ok=True)
    audio, marks = synthesize(TEXT, OUT)
    total = audio_duration(audio)
    cues = phrase_cues(marks, TEXT)
    print(f"voice {total:.2f}s, cues {len(cues)}, net {len(NET)} nodes")

    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))

    n = int(total * FPS)
    ci = 0
    for i in range(n):
        t = i / FPS
        while ci + 1 < len(cues) and cues[ci + 1][0] <= t:
            ci += 1
        word = cues[ci][2] if t >= cues[ci][0] - 0.05 else (cues[ci - 1][2] if ci else "")
        img = Image.new("RGB", (S(W), S(H)), (12, 16, 20))
        d = ImageDraw.Draw(img, "RGBA")
        draw_frame(d, t, total, word)
        img.resize((W, H), Image.LANCZOS).save(os.path.join(frames_dir, f"f{i:05d}.png"))
        if i % 200 == 0:
            print("frame", i, "/", n)

    video = os.path.join(OUT, "video.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames_dir, "f%05d.png"), "-i", audio,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                    video], check=True)
    print("video", video)


if __name__ == "__main__":
    main()
