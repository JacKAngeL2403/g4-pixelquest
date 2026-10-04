"""Paleta fija de colores (estilo consola de 8 bits). El framebuffer guarda
índices de esta lista, no colores RGB."""
from __future__ import annotations

from typing import Dict, List, Tuple

_COLORS: List[Tuple[str, str]] = [
    ("BLACK", "101018"), ("WHITE", "fcfcfc"),
    ("G1", "d8d8d8"), ("G2", "a0a0a8"), ("G3", "686870"), ("G4", "383840"),
    ("BLUE1", "4848c8"), ("BLUE2", "3838a8"), ("BLUE3", "282888"), ("BLUE4", "181868"),
    ("NAVY", "080838"), ("SKY", "78b8f8"), ("CYAN", "58e0e0"), ("TEAL", "208888"),
    ("LGREEN", "88e068"), ("GREEN", "38b038"), ("DGREEN", "186020"), ("LIME", "c8f048"),
    ("YELLOW", "f8e050"), ("GOLD", "e8a820"), ("ORANGE", "f08030"),
    ("LRED", "f86868"), ("RED", "d82828"), ("DRED", "881818"), ("PINK", "f8a0c8"),
    ("LPURPLE", "b878f0"), ("PURPLE", "7838c8"), ("DPURPLE", "401870"),
    ("TAN", "d09858"), ("BROWN", "986028"), ("DBROWN", "582c14"),
    ("SKIN", "f8c898"), ("DSKIN", "d89868"),
    ("STONE1", "585868"), ("STONE2", "40404c"), ("STONE3", "2c2c38"), ("STONE4", "1c1c26"),
    ("NIGHT1", "080818"), ("NIGHT2", "10102c"), ("NIGHT3", "1c1c48"),
    ("GRASS1", "285820"), ("GRASS2", "1c4018"), ("FLOOR1", "504838"), ("FLOOR2", "3c342a"),
]

NAMES: List[str] = [n for n, _ in _COLORS]
RGB: List[Tuple[int, int, int]] = [
    (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)) for _, h in _COLORS
]
TRANSPARENT = 255


class _Colors:
    """C.WHITE -> índice de color. Ej.: fb.rect(0, 0, 10, 10, C.BLUE1)"""


C = _Colors()
for _i, _n in enumerate(NAMES):
    setattr(C, _n, _i)

# Tablas para convertir índices -> canales RGB con bytes.translate (rápido)
TABLE_R = bytes(RGB[i][0] if i < len(RGB) else 0 for i in range(256))
TABLE_G = bytes(RGB[i][1] if i < len(RGB) else 0 for i in range(256))
TABLE_B = bytes(RGB[i][2] if i < len(RGB) else 0 for i in range(256))

# Letras usadas al dibujar sprites como texto -> nombre de color
LEGEND: Dict[str, str] = {
    "k": "BLACK", "w": "WHITE", "a": "G1", "b": "G2", "c": "G3", "d": "G4",
    "r": "RED", "R": "DRED", "q": "LRED", "o": "ORANGE", "y": "YELLOW", "Y": "GOLD",
    "g": "GREEN", "G": "DGREEN", "l": "LGREEN", "L": "LIME",
    "u": "SKY", "e": "CYAN", "t": "TEAL", "U": "BLUE1", "N": "BLUE3",
    "p": "PURPLE", "P": "DPURPLE", "v": "LPURPLE", "m": "PINK",
    "n": "BROWN", "B": "DBROWN", "h": "TAN", "s": "SKIN", "S": "DSKIN",
    "x": "STONE1", "z": "STONE2",
}
