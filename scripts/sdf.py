"""SDF-рендер в numpy: поля расстояний, нормали, шейдинг.

Никаких 3D-движков: сцена задаётся функциями расстояния, нормали берутся
из градиента поля, свет — Ламберт + блик + рим-лайт. Результат — RGBA-массив,
который кладётся в кадр PIL.
"""
import numpy as np


def grid(w, h, x0=0.0, y0=0.0):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    return xs + x0, ys + y0


def sd_ellipse(px, py, cx, cy, rx, ry):
    """Приближённое расстояние до эллипса (достаточно для шейдинга)."""
    dx = (px - cx) / rx
    dy = (py - cy) / ry
    k0 = np.sqrt(dx * dx + dy * dy)
    dx2 = (px - cx) / (rx * rx)
    dy2 = (py - cy) / (ry * ry)
    k1 = np.sqrt(dx2 * dx2 + dy2 * dy2) + 1e-6
    return k0 * (k0 - 1.0) / k1


def sd_circle(px, py, cx, cy, r):
    return np.sqrt((px - cx) ** 2 + (py - cy) ** 2) - r


def sd_round_box(px, py, cx, cy, hw, hh, r):
    qx = np.abs(px - cx) - hw + r
    qy = np.abs(py - cy) - hh + r
    outside = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2)
    inside = np.minimum(np.maximum(qx, qy), 0)
    return outside + inside - r


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def normals(sdf, strength=1.0):
    gy, gx = np.gradient(sdf)
    nx = -gx * strength
    ny = -gy * strength
    nz = np.ones_like(sdf) * 0.85
    ln = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    return nx / ln, ny / ln, nz / ln


def shade(sdf, base, light=(-0.45, -0.75, 0.62), spec_power=26, seam=9.0,
          contour=True, ambient=0.34, spec_gain=0.85, rim_gain=0.22):
    """Возвращает (rgb float 0..1, alpha 0..1) для поля расстояний."""
    nx, ny, nz = normals(sdf)
    lx, ly, lz = light
    ln = (lx * lx + ly * ly + lz * lz) ** 0.5
    lx, ly, lz = lx / ln, ly / ln, lz / ln

    lam = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)
    # полу-Ламберт: мягче тени, читается как ткань
    lam = 0.5 * lam + 0.5

    hx, hy, hz = lx, ly, lz + 1.0
    hn = (hx * hx + hy * hy + hz * hz) ** 0.5
    spec = np.clip(nx * hx / hn + ny * hy / hn + nz * hz / hn, 0.0, 1.0) ** spec_power

    rim = np.clip(1.0 - nz, 0.0, 1.0) ** 2
    ao = np.clip(1.0 + sdf / 60.0, 0.25, 1.0)

    rgb = np.empty(sdf.shape + (3,), dtype=np.float32)
    for i in range(3):
        rgb[..., i] = base[i] * (ambient + (1 - ambient) * lam) * ao
    rgb += spec[..., None] * spec_gain
    rgb += rim[..., None] * rim_gain * np.array([0.55, 0.75, 0.95], dtype=np.float32)

    if contour:
        band = np.abs((sdf % seam) - seam * 0.5)
        lines = np.clip(1.0 - band / 0.9, 0.0, 1.0)
        rgb *= (1.0 - 0.28 * lines[..., None])

    alpha = np.clip(-sdf / 1.2, 0.0, 1.0)
    return np.clip(rgb, 0.0, 1.0), alpha


def to_rgba(sdf, base, **kw):
    rgb, alpha = shade(sdf, base, **kw)
    out = np.empty(sdf.shape + (4,), dtype=np.uint8)
    out[..., :3] = (rgb * 255).astype(np.uint8)
    out[..., 3] = (alpha * 255).astype(np.uint8)
    return out
