"""Sprites pixel-art de 16x16 (y 8x8 para iconos), dibujados por código.

Cada sprite se construye sobre una cuadrícula con `Grid` y al final se le añade
un contorno negro automático. Las letras son colores (ver palette.LEGEND).
"""
from __future__ import annotations

from typing import Dict

from .framebuffer import Sprite


class Grid:
    def __init__(self, w: int = 16, h: int = 16) -> None:
        self.w, self.h = w, h
        self.g = [["."] * w for _ in range(h)]

    def px(self, x: int, y: int, c: str) -> "Grid":
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = c
        return self

    def rect(self, x: int, y: int, w: int, h: int, c: str) -> "Grid":
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(xx, yy, c)
        return self

    def put(self, x: int, y: int, rows: str) -> "Grid":
        """Pega filas de texto (separadas por '/'); '.' no borra lo que había."""
        for j, row in enumerate(rows.split("/")):
            for i, ch in enumerate(row):
                if ch != ".":
                    self.px(x + i, y + j, ch)
        return self

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, c: str) -> "Grid":
        for y in range(self.h):
            for x in range(self.w):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.px(x, y, c)
        return self

    def outlined(self, color: str = "k") -> "Grid":
        """Añade un borde de 1 píxel alrededor de lo dibujado."""
        out = [row[:] for row in self.g]
        for y in range(self.h):
            for x in range(self.w):
                if self.g[y][x] != ".":
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h and self.g[ny][nx] != ".":
                        out[y][x] = color
                        break
        self.g = out
        return self

    def sprite(self) -> Sprite:
        return Sprite(["".join(r) for r in self.g])


# ------------------------------------------------------------------ HÉROES
def _body(g: Grid, hair: str, skin: str, tunic: str, tunic_d: str, pants: str, boots: str) -> Grid:
    """Cuerpo 'chibi' base: cabeza, torso, brazos y piernas."""
    g.rect(4, 3, 8, 5, skin)                 # cabeza
    g.rect(4, 3, 8, 2, hair)                 # pelo
    g.px(4, 5, hair).px(11, 5, hair)
    g.px(6, 6, "k").px(9, 6, "k")            # ojos
    g.rect(4, 8, 8, 4, tunic)                # torso
    g.rect(4, 11, 8, 1, tunic_d)             # cinturón
    g.rect(3, 8, 1, 3, tunic).rect(12, 8, 1, 3, tunic)  # brazos
    g.px(3, 11, skin).px(12, 11, skin)       # manos
    g.rect(5, 12, 3, 2, pants).rect(8, 12, 3, 2, pants)  # piernas
    g.rect(5, 14, 3, 1, boots).rect(8, 14, 3, 1, boots)  # botas
    return g


def warrior() -> Sprite:
    g = _body(Grid(), "n", "s", "r", "R", "N", "B")
    g.rect(4, 3, 8, 3, "b").rect(5, 3, 3, 1, "a")           # casco
    g.rect(4, 6, 1, 2, "b").rect(11, 6, 1, 2, "b")
    g.rect(7, 1, 2, 2, "r").px(6, 2, "r").px(9, 2, "R")      # penacho
    g.rect(5, 8, 6, 3, "b").rect(5, 8, 6, 1, "a")            # peto
    g.rect(13, 1, 1, 8, "a").px(13, 0, "w")                  # espada
    g.rect(12, 9, 3, 1, "Y").px(13, 10, "n").px(12, 11, "s")
    g.rect(0, 7, 4, 6, "U").rect(1, 8, 2, 4, "N").px(1, 9, "Y").px(2, 9, "Y")   # escudo
    g.px(1, 10, "Y").px(2, 10, "Y")
    return g.outlined().sprite()


def mage() -> Sprite:
    g = Grid()
    g.rect(4, 4, 8, 4, "s")                                   # cara
    g.px(6, 6, "k").px(9, 6, "k")
    g.rect(5, 7, 6, 1, "w")                                   # barba
    g.rect(4, 8, 8, 4, "U").rect(3, 12, 10, 3, "U")           # túnica
    g.rect(4, 11, 8, 1, "Y")
    g.rect(3, 8, 1, 3, "U").rect(12, 8, 1, 3, "U").px(3, 11, "s").px(12, 11, "s")
    g.rect(5, 13, 6, 2, "N")
    g.px(8, 1, "p").rect(7, 2, 3, 1, "p").rect(6, 3, 5, 1, "p").rect(2, 4, 12, 1, "P")  # sombrero
    g.px(8, 2, "y").px(7, 3, "P")
    g.rect(1, 3, 1, 12, "n").rect(0, 1, 3, 3, "e").px(1, 2, "w")   # bastón + orbe
    return g.outlined().sprite()


def rogue() -> Sprite:
    g = _body(Grid(), "G", "s", "G", "B", "z", "B")
    g.rect(4, 3, 8, 3, "G").rect(4, 5, 1, 3, "G").rect(11, 5, 1, 3, "G")   # capucha
    g.rect(5, 3, 3, 1, "g")
    g.rect(5, 6, 6, 1, "k").px(6, 6, "y").px(9, 6, "y")       # antifaz y ojos
    g.rect(5, 7, 6, 1, "s")
    g.rect(5, 8, 6, 3, "n").rect(4, 8, 1, 3, "G").rect(11, 8, 1, 3, "G")  # chaleco
    g.rect(13, 7, 1, 4, "a").px(13, 6, "w").px(13, 11, "n")   # daga derecha
    g.rect(2, 8, 1, 3, "a").px(2, 7, "w").px(2, 11, "n")      # daga izquierda
    return g.outlined().sprite()


def cleric() -> Sprite:
    g = _body(Grid(), "Y", "s", "w", "a", "w", "n")
    g.rect(6, 1, 4, 3, "w").rect(4, 3, 8, 1, "w")             # mitra
    g.px(7, 2, "r").px(8, 2, "r").px(7, 1, "r").px(8, 1, "r")
    g.px(7, 3, "r").px(8, 3, "r")
    g.rect(4, 4, 1, 3, "Y").rect(11, 4, 1, 3, "Y")             # pelo dorado
    g.rect(5, 8, 6, 1, "y").rect(7, 9, 2, 3, "y")              # estola
    g.rect(3, 12, 10, 2, "w").rect(3, 13, 10, 1, "a")          # falda de la túnica
    g.rect(13, 3, 1, 11, "Y").rect(12, 1, 3, 3, "Y").px(13, 2, "q")   # báculo
    return g.outlined().sprite()


def archer() -> Sprite:
    g = _body(Grid(), "n", "s", "g", "n", "n", "B")
    g.rect(4, 2, 8, 2, "G").rect(5, 1, 6, 1, "G").rect(3, 4, 10, 1, "g")   # gorro
    g.rect(11, 0, 1, 3, "r").px(12, 1, "r")                    # pluma
    g.rect(11, 6, 3, 5, "n").px(11, 5, "a").px(13, 5, "a").px(12, 4, "a")   # carcaj
    g.rect(1, 3, 1, 10, "n").px(2, 2, "n").px(2, 13, "n")      # arco
    g.rect(2, 3, 1, 10, "a")                                   # cuerda
    return g.outlined().sprite()


def knight() -> Sprite:
    g = _body(Grid(), "b", "b", "b", "c", "c", "z")
    g.rect(4, 3, 8, 5, "b").rect(5, 3, 3, 1, "a")              # yelmo cerrado
    g.rect(5, 5, 6, 1, "k").rect(7, 5, 2, 3, "k")              # visera
    g.rect(7, 0, 2, 3, "U").px(6, 2, "U")                      # penacho
    g.rect(4, 8, 8, 4, "b").rect(5, 8, 6, 3, "U").rect(7, 9, 2, 2, "Y")   # armadura + tabardo
    g.rect(4, 11, 8, 1, "c")
    g.rect(12, 8, 1, 3, "b").px(12, 11, "a")
    g.rect(0, 6, 4, 8, "b").rect(1, 7, 2, 6, "U").rect(1, 9, 2, 2, "Y")   # escudo grande
    g.rect(13, 5, 1, 6, "a").px(13, 4, "w").rect(12, 11, 3, 1, "Y")        # espada corta
    return g.outlined().sprite()


def alchemist() -> Sprite:
    g = _body(Grid(), "o", "s", "w", "a", "z", "B")
    g.rect(4, 3, 8, 2, "o").px(5, 2, "o").px(7, 2, "o").px(9, 2, "o").px(11, 2, "o")   # pelo
    g.px(6, 1, "o").px(10, 1, "o")
    g.rect(5, 5, 6, 1, "n").px(5, 5, "e").px(6, 5, "e").px(9, 5, "e").px(10, 5, "e")   # gafas
    g.rect(4, 8, 8, 4, "w").rect(7, 8, 2, 4, "a")              # bata
    g.rect(3, 8, 1, 3, "w").rect(12, 8, 1, 3, "w").px(3, 11, "l").px(12, 11, "l")
    g.rect(13, 10, 3, 3, "e").rect(13, 11, 3, 2, "l").px(14, 9, "n")    # frasco
    g.rect(4, 11, 8, 1, "b")
    return g.outlined().sprite()


# ---------------------------------------------------------------- ENEMIGOS
def slime(body: str = "g", light: str = "l", dark: str = "G", crown: bool = False) -> Sprite:
    g = Grid()
    g.ellipse(7.5, 10.5, 6.6, 4.4, body)
    g.rect(2, 12, 12, 3, body)
    g.rect(3, 6, 6, 1, light).rect(4, 5, 3, 1, light).px(4, 7, light).px(3, 8, light)
    g.rect(2, 14, 12, 1, dark).rect(3, 13, 1, 1, dark).rect(12, 13, 1, 1, dark)
    g.rect(5, 9, 2, 3, "w").rect(9, 9, 2, 3, "w").rect(6, 10, 1, 2, "k").rect(10, 10, 1, 2, "k")
    g.rect(7, 13, 2, 1, "k")
    if crown:
        g.rect(4, 3, 8, 2, "Y").px(4, 2, "Y").px(7, 2, "Y").px(11, 2, "Y").px(8, 3, "r")
    return g.outlined().sprite()


def goblin(skin: str = "g", light: str = "l", crown: bool = False) -> Sprite:
    g = Grid()
    g.rect(4, 3, 8, 6, skin).rect(4, 3, 8, 1, light)
    g.put(1, 4, "..gg/.ggg/ggg.").put(13, 4, "gg../ggg./.ggg")     # orejas puntiagudas
    g.px(6, 5, "r").px(9, 5, "r").px(6, 6, "k").px(9, 6, "k")
    g.rect(6, 8, 4, 1, "R").px(6, 7, "w").px(9, 7, "w")
    g.rect(4, 9, 8, 3, "n").rect(5, 9, 6, 1, "h")                    # chaleco
    g.rect(3, 9, 1, 3, skin).rect(12, 9, 1, 3, skin)
    g.rect(5, 12, 6, 1, "B").rect(5, 13, 2, 2, skin).rect(9, 13, 2, 2, skin)
    g.rect(13, 3, 2, 8, "h").rect(13, 2, 2, 2, "n").px(14, 3, "B")   # garrote
    if crown:
        g.rect(5, 1, 6, 2, "Y").px(5, 0, "Y").px(8, 0, "Y").px(10, 0, "Y")
    return g.outlined().sprite()


def skeleton() -> Sprite:
    g = Grid()
    g.rect(5, 1, 6, 5, "w").rect(6, 6, 4, 1, "w")                     # cráneo
    g.rect(6, 3, 2, 2, "k").rect(9, 3, 2, 2, "k").px(8, 5, "k")
    g.rect(6, 6, 4, 1, "a").px(7, 6, "k").px(9, 6, "k")               # dientes
    g.rect(7, 7, 2, 1, "a")
    g.rect(4, 8, 8, 1, "w").rect(5, 9, 6, 1, "a").rect(5, 10, 6, 1, "w").rect(6, 11, 4, 1, "a")
    g.rect(7, 8, 2, 4, "w")
    g.rect(3, 8, 1, 4, "a").rect(12, 8, 1, 4, "a")
    g.rect(6, 12, 1, 3, "w").rect(9, 12, 1, 3, "w").rect(5, 14, 2, 1, "a").rect(9, 14, 2, 1, "a")
    g.rect(14, 4, 1, 8, "b").px(14, 3, "a").rect(13, 11, 3, 1, "n")     # espada oxidada
    return g.outlined().sprite()


def wolf() -> Sprite:
    """Lobo mirando a la derecha."""
    g = Grid()
    g.rect(2, 6, 9, 5, "P").rect(3, 5, 7, 1, "z")                    # cuerpo
    g.rect(9, 3, 5, 5, "P").rect(13, 5, 2, 3, "z")                   # cabeza + hocico
    g.px(9, 2, "P").px(10, 1, "P").px(12, 2, "P").px(12, 1, "P")     # orejas
    g.px(12, 4, "y").px(13, 4, "y").px(14, 7, "k")
    g.rect(13, 8, 2, 1, "w")                                          # colmillo
    g.rect(2, 11, 2, 3, "P").rect(5, 11, 2, 3, "P").rect(8, 11, 2, 3, "P")
    g.rect(1, 13, 3, 1, "z").rect(7, 13, 3, 1, "z")
    g.rect(0, 4, 2, 2, "P").px(0, 3, "P").px(1, 6, "P")               # cola
    g.rect(4, 6, 5, 1, "v")                                           # brillo del lomo
    return g.outlined().sprite()


def bat() -> Sprite:
    g = Grid()
    g.put(0, 3, "P.........P.../PP.......PP../PpP.....PpP../PppP...PppP../PpppP.PpppP./PpPpPPPpPpP./.P.PppppP.P./....PppP..../.....PP.....")
    g.rect(6, 4, 4, 6, "p").rect(7, 3, 2, 1, "p").px(6, 2, "p").px(9, 2, "p")
    g.px(7, 6, "r").px(9, 6, "r").px(7, 8, "w").px(9, 8, "w")
    g.put(0, 3, "")
    return g.outlined().sprite()


def ghost() -> Sprite:
    g = Grid()
    g.rect(4, 2, 8, 11, "w").rect(5, 1, 6, 1, "w").rect(3, 5, 10, 7, "w")
    g.rect(4, 4, 1, 8, "a").rect(11, 4, 1, 8, "a").rect(3, 12, 10, 1, "a")
    g.put(3, 13, "w.w.w.w.w./.a.a.a.a..")
    g.rect(5, 5, 2, 3, "k").rect(9, 5, 2, 3, "k").px(6, 6, "e").px(10, 6, "e")
    g.rect(7, 9, 2, 2, "k")
    g.rect(1, 6, 2, 3, "w").rect(13, 6, 2, 3, "w")                    # brazos
    return g.outlined().sprite()


def orc() -> Sprite:
    g = Grid()
    g.rect(4, 2, 8, 6, "G").rect(4, 2, 8, 1, "g")
    g.rect(5, 4, 2, 1, "k").rect(9, 4, 2, 1, "k").px(6, 4, "r").px(10, 4, "r")   # ojos
    g.rect(5, 6, 6, 2, "G").px(5, 6, "w").px(10, 6, "w").px(5, 5, "w").px(10, 5, "w")  # colmillos
    g.rect(2, 8, 12, 4, "z").rect(3, 8, 10, 1, "x").rect(2, 8, 2, 2, "b").rect(12, 8, 2, 2, "b")   # hombreras
    g.rect(6, 9, 4, 3, "n").rect(1, 9, 2, 4, "G").rect(13, 9, 2, 4, "G")
    g.rect(4, 12, 3, 3, "G").rect(9, 12, 3, 3, "G").rect(4, 14, 3, 1, "B").rect(9, 14, 3, 1, "B")
    g.rect(0, 2, 1, 9, "n").rect(0, 1, 3, 3, "b").px(1, 2, "a")        # hacha
    return g.outlined().sprite()


def dragon() -> Sprite:
    g = Grid()
    g.put(0, 2, "R...........R.../RR.........RR../RrR.......RrR../RrrR.....RrrR./RrqrR...RrqrR./.RrrrRRRRrrrR../..RRrrrrrrrRR.../")
    g.rect(5, 6, 6, 7, "r").rect(4, 8, 8, 4, "r")                    # cuerpo
    g.rect(6, 8, 4, 5, "Y").rect(6, 9, 4, 1, "y").rect(6, 11, 4, 1, "y")   # panza
    g.rect(5, 1, 6, 5, "r").rect(4, 3, 8, 2, "r").rect(6, 5, 4, 2, "q")     # cabeza + hocico
    g.px(5, 0, "w").px(10, 0, "w").px(4, 1, "w").px(11, 1, "w")             # cuernos
    g.px(6, 3, "y").px(9, 3, "y").px(6, 4, "k").px(9, 4, "k")
    g.px(7, 5, "R").px(8, 5, "R").px(6, 6, "w").px(9, 6, "w")
    g.rect(4, 12, 3, 3, "r").rect(9, 12, 3, 3, "r").rect(4, 14, 3, 1, "w").rect(9, 14, 3, 1, "w")
    g.rect(11, 12, 4, 2, "r").px(14, 11, "r").px(15, 10, "R")               # cola
    return g.outlined().sprite()


def golem() -> Sprite:
    g = Grid()
    g.rect(5, 1, 6, 5, "x").rect(5, 1, 6, 1, "b").rect(5, 2, 1, 3, "b")
    g.rect(6, 3, 2, 1, "y").rect(9, 3, 2, 1, "y")                     # ojos brillantes
    g.rect(3, 6, 10, 5, "x").rect(3, 6, 10, 1, "b").rect(4, 8, 8, 1, "z")
    g.rect(2, 6, 2, 3, "b").rect(12, 6, 2, 3, "b")                    # hombros
    g.rect(0, 8, 3, 6, "x").rect(13, 8, 3, 6, "x").rect(0, 12, 3, 2, "z").rect(13, 12, 3, 2, "z")
    g.rect(5, 11, 3, 4, "x").rect(8, 11, 3, 4, "x").rect(5, 14, 3, 1, "z").rect(8, 14, 3, 1, "z")
    g.px(7, 8, "L").px(8, 8, "L").px(7, 9, "g").px(8, 9, "g")          # runa de energía
    g.px(4, 7, "z").px(11, 10, "z").px(6, 5, "z")
    return g.outlined().sprite()


def lich() -> Sprite:
    g = Grid()
    g.rect(5, 1, 6, 6, "P").rect(4, 3, 8, 4, "P")                     # capucha
    g.rect(6, 3, 4, 4, "k").px(7, 4, "e").px(9, 4, "e").rect(7, 6, 2, 1, "w")   # cara vacía
    g.rect(5, 0, 6, 1, "Y").px(5, -1, "Y")                            # corona
    g.px(5, 0, "Y").px(7, 0, "Y").px(9, 0, "Y").px(10, 0, "Y")
    g.rect(3, 7, 10, 7, "P").rect(2, 10, 12, 5, "P").rect(4, 9, 8, 1, "p")
    g.rect(7, 8, 2, 6, "z")
    g.rect(1, 8, 2, 3, "P").rect(13, 8, 2, 3, "P").px(1, 11, "w").px(14, 11, "w")
    g.rect(14, 2, 1, 12, "n").rect(13, 0, 3, 3, "v").px(14, 1, "w")     # báculo
    g.rect(4, 14, 8, 1, "p")
    return g.outlined().sprite()


# ------------------------------------------------------------------ ÍCONOS
def _icon(rows: str) -> Sprite:
    g = Grid(8, 8)
    g.put(0, 0, rows)
    return g.sprite()


ICONS: Dict[str, Sprite] = {
    "weapon": _icon("......aw/.....aw./....aw../.n.aw.../..nw..../..Yn..../.n.Y..../n......."),
    "armor": _icon(".bb..bb./bbbbbbb./bUbbbUb./.bbYbb../.bbbbb../.bbbbb../.bb.bb../........"),
    "potion": _icon("...nn.../...aa.../..aaaa../.arrrra./.arqrra./.arrrra./..aaaa../........"),
    "ether": _icon("...nn.../...aa.../..aaaa../.auuuua./.aueuua./.auuuua./..aaaa../........"),
    "accessory": _icon("..yyyy../.y....y./.y....y./.y....y./..yyyy../...ee.../..eeee../...ee..."),
    "coin": _icon("..yyyy../.yYYYYy./yYyyyyYy/yYyYYyYy/yYyYYyYy/yYyyyyYy/.yYYYYy./..yyyy.."),
    "heart": _icon(".rr..rr./rqrrrrrr/rrrrrrrr/rrrrrrrr/.rrrrrr./..rrrr../...rr.../........"),
}

_cache: Dict[str, Sprite] = {}


# --------------------------------------------------------- OBJETOS DE ESCENA
def chest() -> Sprite:
    g = Grid()
    g.rect(2, 6, 12, 8, "n").rect(2, 6, 12, 3, "h").rect(2, 9, 12, 1, "B")
    g.rect(2, 4, 12, 3, "n").rect(3, 3, 10, 1, "n").rect(2, 4, 12, 1, "h")
    g.rect(2, 4, 1, 10, "Y").rect(13, 4, 1, 10, "Y").rect(7, 8, 2, 3, "y").px(7, 9, "k")
    g.rect(5, 2, 1, 1, "y").px(10, 1, "w").px(12, 3, "y")
    return g.outlined().sprite()


def fountain() -> Sprite:
    g = Grid()
    g.rect(1, 11, 14, 4, "b").rect(2, 10, 12, 1, "a").rect(2, 12, 12, 1, "c")
    g.rect(3, 11, 10, 1, "u").rect(4, 12, 8, 1, "e")
    g.rect(7, 4, 2, 7, "b").rect(5, 3, 6, 1, "b")
    g.px(7, 1, "e").px(8, 0, "u").px(6, 2, "u").px(9, 2, "e").px(5, 4, "u").px(10, 4, "u")
    g.px(4, 6, "e").px(11, 6, "e")
    return g.outlined().sprite()


def spikes() -> Sprite:
    g = Grid()
    g.rect(1, 13, 14, 2, "z")
    for x in (2, 5, 8, 11):
        g.put(x, 8, ".a./.a./aab/aab/aab")
    return g.outlined().sprite()


SCENE = {"chest": chest, "fountain": fountain, "spikes": spikes}


def scene_sprite(name: str) -> Sprite:
    key = "scene:" + name
    if key not in _cache:
        _cache[key] = SCENE[name]()
    return _cache[key]


# ---------------------------------------------------------------- CATÁLOGOS
_HERO_BUILDERS = {
    "warrior": warrior, "mage": mage, "rogue": rogue,
    "cleric": cleric, "archer": archer, "knight": knight, "alchemist": alchemist,
}


def member_sprite(class_key: str) -> Sprite:
    """Sprite de un héroe o compañero según su CLASS_KEY."""
    if class_key not in _cache:
        _cache[class_key] = _HERO_BUILDERS[class_key]()
    return _cache[class_key]


# nombre del enemigo (sin " Nv3") -> (sprite, escala)
def enemy_sprite(name: str, is_boss: bool = False):
    base = name.split(" Nv")[0]
    key = "enemy:" + base
    if key not in _cache:
        table = {
            "Slime": slime,
            "Goblin": goblin,
            "Murciélago": bat,
            "Esqueleto": skeleton,
            "Lobo Sombrío": wolf,
            "Fantasma": ghost,
            "Orco": orc,
            "Rey Slime": lambda: slime("U", "u", "N", crown=True),
            "Señor Goblin": lambda: goblin("o", "y", crown=True),
            "Dragón Pixelado": dragon,
            "Golem de Piedra": golem,
            "Lich Pixelado": lich,
        }
        _cache[key] = table.get(base, slime)()
    return _cache[key], (6 if is_boss else 4)
