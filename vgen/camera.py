"""Кинокамера: движение внутри кадра — наезды, панорамы, тряска, склейки.

Работает поверх любого рендерера: кадр рисуется крупнее (VGEN_SS), а камера
вырезает из него окно и ведёт его по сцене. Смена «плана» внутри сцены даёт
ощущение монтажа, как в фильме.

Важно: зум и панорама ограничены, чтобы заголовки и подписи у краёв не
обрезались — максимум 12% кропа.
"""
import math

# (имя, зум от, зум до, центр от, центр до)
PLANS = [
    ("push", 1.00, 1.12, (0.50, 0.52), (0.50, 0.46)),
    ("pan", 1.10, 1.02, (0.44, 0.50), (0.56, 0.50)),
    ("tilt", 1.04, 1.12, (0.50, 0.56), (0.50, 0.46)),
    ("pull", 1.12, 1.01, (0.54, 0.48), (0.46, 0.52)),
    ("drift", 1.06, 1.10, (0.47, 0.53), (0.53, 0.47)),
]


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def _shot(idx, sub, t01):
    kind, z0, z1, c0, c1 = PLANS[(idx * 2 + sub) % len(PLANS)]
    k = ease(t01)
    z = z0 + (z1 - z0) * k
    cx = c0[0] + (c1[0] - c0[0]) * k
    cy = c0[1] + (c1[1] - c0[1]) * k
    # «ручная» камера: микро-дрожание
    cx += 0.004 * math.sin(t01 * 10.0 + idx)
    cy += 0.003 * math.cos(t01 * 8.0 + idx * 1.7)
    return z, cx, cy


def framing(idx, t_in_scene, dur):
    """-> (zoom, cx, cy). Склейка внутри сцены: два плана, стык на 52%."""
    p = 0.0 if dur <= 0 else max(0.0, min(1.0, t_in_scene / dur))
    cut = 0.52
    if p < cut:
        return _shot(idx, 0, p / cut)
    return _shot(idx, 1, (p - cut) / (1 - cut))


def crop_box(framing_vals, iw, ih):
    z, cx, cy = framing_vals
    z = max(1.0, min(1.12, z))
    w = iw / z
    h = ih / z
    x = cx * iw - w / 2
    y = cy * ih - h / 2
    x = max(0.0, min(iw - w, x))
    y = max(0.0, min(ih - h, y))
    return int(x), int(y), int(x + w), int(y + h)
