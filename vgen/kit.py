"""Общий слой рисования на Skia: градиенты, мягкие тени, свечение, текст с обводкой.

Заменяет россыпь `d.rectangle/d.line` в рендерерах. Координаты — в пикселях
выходного кадра (по умолчанию 1080x1920), антиалиасинг и блюр — настоящие.

    cv = Canvas()
    cv.rrect(40, 40, 300, 120, 16, fill=lin(0, 40, 0, 160, [(0, "#fff"), (1, "#889")]),
             shadow=(0, 8, 14, "#000a"))
    img = cv.to_pil()
"""
import skia
from PIL import Image

from vgen.palette import font_path

W, H = 1080, 1920

_TF = {}
_IMG = {}


def rgba(c, a=None):
    """'#rgb' | '#rrggbb' | '#rrggbbaa' | (r,g,b[,a]) -> skia color int."""
    if isinstance(c, int):
        return c
    if isinstance(c, str):
        s = c.lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        if len(s) == 4:
            s = "".join(ch * 2 for ch in s)
        r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        al = int(s[6:8], 16) if len(s) >= 8 else 255
    else:
        r, g, b = c[0], c[1], c[2]
        al = c[3] if len(c) > 3 else 255
    if a is not None:
        al = int(255 * a)
    return skia.ColorSetARGB(al, r, g, b)


def lin(x0, y0, x1, y1, stops):
    """Линейный градиент; stops = [(pos, color), ...]."""
    return skia.GradientShader.MakeLinear(
        [skia.Point(x0, y0), skia.Point(x1, y1)],
        [rgba(c) for _, c in stops], [p for p, _ in stops])


def rad(cx, cy, r, stops):
    """Радиальный градиент."""
    return skia.GradientShader.MakeRadial(
        skia.Point(cx, cy), r, [rgba(c) for _, c in stops], [p for p, _ in stops])


def _paint(fill=None, stroke=None, width=1.0, blur=0.0, shadow=None, cap="round", alpha=None):
    p = skia.Paint(AntiAlias=True)
    col = stroke if stroke is not None else fill
    if col is not None:
        if isinstance(col, skia.Shader):
            p.setShader(col)
        else:
            p.setColor(rgba(col, alpha))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(width)
        p.setStrokeCap({"round": skia.Paint.kRound_Cap, "butt": skia.Paint.kButt_Cap,
                        "square": skia.Paint.kSquare_Cap}[cap])
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shadow:
        dx, dy, sg, sc = shadow
        p.setImageFilter(skia.ImageFilters.DropShadow(dx, dy, sg, sg, rgba(sc)))
    return p


def typeface():
    if "b" not in _TF:
        _TF["b"] = skia.Typeface.MakeFromFile(font_path())
    return _TF["b"]


class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.surface = skia.Surface(w, h)
        self.c = self.surface.getCanvas()

    # --- состояние -------------------------------------------------------
    def save(self):
        self.c.save()

    def restore(self):
        self.c.restore()

    def zoom(self, s, cx, cy):
        self.c.translate(cx, cy)
        self.c.scale(s, s)
        self.c.translate(-cx, -cy)

    def rotate(self, deg, px, py):
        self.c.rotate(deg, px, py)

    # --- примитивы -------------------------------------------------------
    def clear(self, color):
        self.c.clear(rgba(color))

    def rect(self, x0, y0, x1, y1, **kw):
        self.c.drawRect(skia.Rect(x0, y0, x1, y1), _paint(**kw))

    def rrect(self, x0, y0, x1, y1, r, **kw):
        self.c.drawRoundRect(skia.Rect(x0, y0, x1, y1), r, r, _paint(**kw))

    def circle(self, x, y, r, **kw):
        self.c.drawCircle(x, y, r, _paint(**kw))

    def oval(self, x0, y0, x1, y1, **kw):
        self.c.drawOval(skia.Rect(x0, y0, x1, y1), _paint(**kw))

    def line(self, x0, y0, x1, y1, color, width=2.0, **kw):
        self.c.drawLine(x0, y0, x1, y1, _paint(stroke=color, width=width, **kw))

    def poly(self, pts, close=True, **kw):
        path = skia.Path()
        path.moveTo(*pts[0])
        for p in pts[1:]:
            path.lineTo(*p)
        if close:
            path.close()
        self.c.drawPath(path, _paint(**kw))

    def path(self, path, **kw):
        self.c.drawPath(path, _paint(**kw))

    # --- текст -----------------------------------------------------------
    def font(self, size):
        return skia.Font(typeface(), size)

    def text_w(self, s, size):
        return self.font(size).measureText(s)

    def text(self, s, x, y, size, fill="#fff", stroke=None, stroke_w=0, glow=None,
             shadow=None, center=False, alpha=None):
        """Текст с опциональной обводкой, свечением и тенью. y — базовая линия."""
        f = self.font(size)
        if center:
            x = x - f.measureText(s) / 2
        if glow:
            gc, gr = glow
            self.c.drawString(s, x, y, f, _paint(fill=gc, blur=gr, alpha=alpha))
        if stroke is not None and stroke_w:
            sp = _paint(stroke=stroke, width=stroke_w, shadow=shadow, alpha=alpha)
            self.c.drawString(s, x, y, f, sp)
            shadow = None
        self.c.drawString(s, x, y, f, _paint(fill=fill, shadow=shadow, alpha=alpha))

    # --- клип, изображения, карточки -------------------------------------
    def clip(self, x0, y0, x1, y1):
        self.c.clipRect(skia.Rect(x0, y0, x1, y1))

    def image_cover(self, path, zoom=1.0, pan=(0.0, 0.0), alpha=1.0):
        """Картинка «cover» на весь холст с зумом/панорамой (pan в долях −1..1)."""
        img = _IMG.get(path)
        if img is None:
            img = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(path))
            _IMG[path] = img
        iw, ih = img.width(), img.height()
        sc = max(self.w / iw, self.h / ih) * zoom
        dw, dh = iw * sc, ih * sc
        x = (self.w - dw) / 2 + pan[0] * (dw - self.w) / 2
        y = (self.h - dh) / 2 + pan[1] * (dh - self.h) / 2
        p = skia.Paint(AntiAlias=True)
        p.setAlphaf(alpha)
        self.c.drawImageRect(img, skia.Rect(x, y, x + dw, y + dh), skia.SamplingOptions(skia.FilterMode.kLinear), p)

    def card(self, x0, y0, x1, y1, accent="#7fe4ff", r=26, alpha=0.82, glow=False, a=1.0):
        """Стеклянная карточка: тёмная подложка, световая кромка сверху, тень."""
        self.rrect(x0, y0, x1, y1, r, fill=lin(0, y0, 0, y1, [(0, "#16233f"), (1, "#0a1224")]),
                   shadow=(0, 10, 16, "#000a"), alpha=alpha * a)
        self.rrect(x0, y0, x1, y1, r, stroke=accent, width=2.5, alpha=0.75 * a)
        self.line(x0 + r, y0 + 2, x1 - r, y0 + 2, "#ffffff", 2, alpha=0.28 * a)
        if glow:
            self.rrect(x0, y0, x1, y1, r, stroke=accent, width=6, blur=10, alpha=0.5 * a)

    # --- вывод -----------------------------------------------------------
    def to_pil(self):
        arr = self.surface.makeImageSnapshot().toarray(
            colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
        return Image.fromarray(arr[..., :3].copy(), "RGB")


# --- составные «материалы» ---------------------------------------------------

def tube(cv, x0, y0, x1, y1, w, base="#f2b624", dark="#8a5a08", light="#ffe9a0", glow=True):
    """Трубка/профиль с объёмом: тень, основной цвет, световая кромка."""
    if glow:
        cv.line(x0 + 1.5, y0 + 2.5, x1 + 1.5, y1 + 2.5, "#00000070", w + 2, blur=2.2)
    cv.line(x0, y0, x1, y1, dark, w)
    cv.line(x0, y0, x1, y1, base, max(1.0, w - 1.6))
    cv.line(x0 + 0.4, y0 - w * 0.22, x1 + 0.4, y1 - w * 0.22, light, max(0.8, w * 0.28), alpha=0.8)


def truss(cv, x0, y0, x1, y1, depth, cells, w=5, base="#f2b624", dark="#8a5a08",
          light="#ffe9a0", web_w=None, rungs=False):
    """Решётчатая ферма от (x0,y0) к (x1,y1), depth — высота сечения (в плоскости)."""
    import math
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    a = (x0 + nx * depth / 2, y0 + ny * depth / 2)
    b = (x0 - nx * depth / 2, y0 - ny * depth / 2)
    web_w = web_w or max(2.0, w * 0.55)
    pts_a, pts_b = [], []
    for i in range(cells + 1):
        k = i / cells
        pts_a.append((a[0] + dx * k, a[1] + dy * k))
        pts_b.append((b[0] + dx * k, b[1] + dy * k))
    # диагонали и (опц.) стойки — под поясами
    for i in range(cells):
        p, q = (pts_a[i], pts_b[i + 1]) if i % 2 == 0 else (pts_b[i], pts_a[i + 1])
        tube(cv, p[0], p[1], q[0], q[1], web_w, base, dark, light, glow=False)
        if rungs:
            tube(cv, pts_a[i][0], pts_a[i][1], pts_b[i][0], pts_b[i][1], web_w * 0.8,
                 base, dark, light, glow=False)
    if rungs:
        tube(cv, pts_a[-1][0], pts_a[-1][1], pts_b[-1][0], pts_b[-1][1], web_w * 0.8,
             base, dark, light, glow=False)
    tube(cv, a[0], a[1], a[0] + dx, a[1] + dy, w, base, dark, light)
    tube(cv, b[0], b[1], b[0] + dx, b[1] + dy, w, base, dark, light)
