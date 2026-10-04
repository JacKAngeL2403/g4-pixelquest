"""Fondos pintados por código (cacheados). Devuelven el framebuffer ya dibujado
como bytes para cargarlo de golpe en cada cuadro."""
from __future__ import annotations

import math
import random
from typing import Dict, Tuple

from .framebuffer import H, W, Framebuffer
from .palette import C

_cache: Dict[Tuple, bytes] = {}

# (ladrillo, mortero, brillo, suelo1, suelo2)
THEMES = [
    (C.STONE2, C.STONE4, C.STONE1, C.FLOOR1, C.FLOOR2),      # calabozo
    (C.GRASS2, C.STONE4, C.GRASS1, C.STONE2, C.STONE3),      # cueva con musgo
    (C.DBROWN, C.STONE4, C.BROWN, C.STONE2, C.STONE3),       # minas
    (C.NAVY, C.STONE4, C.BLUE3, C.BLUE4, C.NAVY),            # cripta helada
    (C.DPURPLE, C.STONE4, C.PURPLE, C.STONE3, C.STONE4),     # santuario oscuro
]


def _stars(fb: Framebuffer, count: int, ymax: int, seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(count):
        x, y = rng.randrange(W), rng.randrange(ymax)
        fb.pixel(x, y, rng.choice([C.WHITE, C.G1, C.G2, C.SKY]))


def _sky(fb: Framebuffer, height: int) -> None:
    fb.gradient(0, 0, W, height, [C.NIGHT1, C.NIGHT1, C.NIGHT2, C.NIGHT2, C.NIGHT3, C.NIGHT3])


def camp_bg() -> bytes:
    if ("camp",) in _cache:
        return _cache[("camp",)]
    fb = Framebuffer()
    _sky(fb, 150)
    _stars(fb, 70, 100, 7)
    fb.ellipse(268, 40, 14, 14, C.G1)
    fb.ellipse(272, 37, 12, 12, C.NIGHT2)          # luna creciente
    fb.ellipse(268, 40, 14, 14, C.NIGHT2)
    fb.ellipse(262, 40, 12, 13, C.G1)
    # montañas
    for x in range(W):
        h = 30 + int(14 * math.sin(x / 34.0) + 8 * math.sin(x / 13.0 + 1))
        fb.rect(x, 128 - h, 1, h + 4, C.STONE4)
    for x in range(W):
        h = 14 + int(8 * math.sin(x / 21.0 + 2) + 4 * math.sin(x / 7.0))
        fb.rect(x, 140 - h, 1, h + 10, C.NIGHT1)
    # pinos
    rng = random.Random(3)
    for x in range(6, W, 22):
        h = rng.randint(22, 34)
        base = 142
        for k in range(4):
            fb.rect(x - 6 + k * 2, base - h + k * (h // 4), 12 - k * 4, h // 4 + 1, C.GRASS2)
        fb.rect(x - 1, base, 3, 6, C.DBROWN)
    # suelo
    fb.rect(0, 146, W, H - 146, C.GRASS2)
    for y in range(146, H, 4):
        for x in range((y * 7) % 11, W, 11):
            fb.pixel(x, y, C.GRASS1)
    fb.ellipse(160, 150, 150, 8, C.GRASS1)
    fb.ellipse(160, 152, 120, 6, C.FLOOR2)          # claro de tierra
    # tienda de campaña
    fb.line(232, 120, 214, 148, C.BROWN)
    for i in range(0, 20):
        fb.rect(232 - i, 120 + i * 28 // 20, 2 * i + 1, 2, C.TAN if i % 5 else C.BROWN)
    fb.rect(226, 136, 12, 12, C.DBROWN)
    _cache[("camp",)] = fb.snapshot()
    return _cache[("camp",)]


def title_bg() -> bytes:
    if ("title",) in _cache:
        return _cache[("title",)]
    fb = Framebuffer()
    _sky(fb, H)
    _stars(fb, 110, 150, 11)
    fb.ellipse(250, 60, 22, 22, C.G1)
    fb.ellipse(240, 56, 20, 20, C.NIGHT2)
    fb.ellipse(250, 60, 22, 22, C.NIGHT2)
    fb.ellipse(242, 60, 19, 21, C.G1)
    for x in range(W):
        h = 40 + int(20 * math.sin(x / 40.0) + 10 * math.sin(x / 15.0))
        fb.rect(x, 190 - h, 1, h + 60, C.STONE4)
    # castillo
    fb.rect(70, 130, 60, 60, C.STONE3)
    for tx in (66, 100, 124):
        fb.rect(tx, 108, 12, 82, C.STONE3)
        fb.rect(tx - 2, 104, 16, 5, C.STONE2)
        for k in range(4):
            fb.rect(tx - 2 + k * 5, 99, 3, 5, C.STONE2)
        fb.rect(tx + 4, 116, 4, 8, C.YELLOW)
    fb.rect(96, 160, 8, 30, C.STONE4)
    fb.rect(0, 200, W, 40, C.NIGHT1)
    _cache[("title",)] = fb.snapshot()
    return _cache[("title",)]


def dungeon_bg(floor: int) -> bytes:
    theme = (floor - 1) % len(THEMES)
    key = ("dungeon", theme)
    if key in _cache:
        return _cache[key]
    brick, mortar, shine, f1, f2 = THEMES[theme]
    fb = Framebuffer()
    wall_h = 112
    fb.rect(0, 0, W, wall_h, brick)
    for row in range(0, wall_h, 14):
        fb.hline(0, row, W, mortar)
        off = 0 if (row // 14) % 2 == 0 else 12
        for x in range(-off, W, 24):
            fb.vline(x, row, 14, mortar)
            fb.hline(x + 1, row + 1, 22, shine)
    fb.rect(0, wall_h, W, 4, mortar)
    # suelo con baldosas en perspectiva simple
    fb.rect(0, wall_h + 4, W, H - wall_h - 4, f1)
    y = wall_h + 4
    step = 6
    while y < H:
        fb.hline(0, y, W, f2)
        y += step
        step += 3
    for i in range(-6, 14):
        fb.line(160 + (i - 4) * 12, wall_h + 4, 160 + (i - 4) * 46, H, f2)
    # arcos/antorchas
    for tx in (44, 160, 276):
        fb.rect(tx - 2, 44, 5, 10, C.DBROWN)
        fb.rect(tx - 3, 42, 7, 3, C.G3)
    _cache[key] = fb.snapshot()
    return _cache[key]


def draw_torches(fb: Framebuffer, t: float) -> None:
    for i, tx in enumerate((44, 160, 276)):
        f = int(t * 8 + i * 3) % 3
        fb.rect(tx - 2, 36 - f, 5, 6 + f, C.ORANGE)
        fb.rect(tx - 1, 34 - f, 3, 6 + f, C.YELLOW)
        fb.pixel(tx, 32 - f, C.YELLOW)


def draw_campfire(fb: Framebuffer, x: int, y: int, t: float) -> None:
    fb.rect(x - 12, y + 6, 24, 4, C.DBROWN)
    fb.rect(x - 9, y + 3, 18, 3, C.BROWN)
    f = int(t * 9) % 3
    fb.rect(x - 7, y - 4, 14, 8, C.RED)
    fb.rect(x - 5, y - 9 - f, 10, 12 + f, C.ORANGE)
    fb.rect(x - 3, y - 14 - f, 6, 14 + f, C.YELLOW)
    fb.rect(x - 1, y - 6, 2, 6, C.WHITE)
    for k in range(3):                              # chispas
        sx = x - 6 + ((int(t * 6) * 5 + k * 7) % 13)
        sy = y - 20 - ((int(t * 12) + k * 4) % 12)
        fb.pixel(sx, sy, C.YELLOW)
