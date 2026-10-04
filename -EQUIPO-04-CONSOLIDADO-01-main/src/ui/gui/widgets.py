"""Componentes de interfaz estilo JRPG de 8 bits: ventanas, barras, menús con
cursor y cuadros de diálogo con efecto máquina de escribir."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from . import font
from .framebuffer import Framebuffer
from .palette import C
from .sprites import ICONS


def window(fb: Framebuffer, x: int, y: int, w: int, h: int) -> None:
    """Ventana azul con degradado y borde blanco de esquinas cortadas."""
    fb.rect(x + 2, y + h, w - 2, 1, C.BLACK)      # sombra
    fb.rect(x + w, y + 2, 1, h - 1, C.BLACK)
    fb.gradient(x + 1, y + 1, w - 2, h - 2, [C.BLUE1, C.BLUE2, C.BLUE3, C.BLUE4])
    fb.hline(x + 1, y, w - 2, C.WHITE)
    fb.hline(x + 1, y + h - 1, w - 2, C.WHITE)
    fb.vline(x, y + 1, h - 2, C.WHITE)
    fb.vline(x + w - 1, y + 1, h - 2, C.WHITE)
    fb.pixel(x + 1, y + 1, C.G2)
    fb.pixel(x + w - 2, y + 1, C.G2)
    fb.pixel(x + 1, y + h - 2, C.G2)
    fb.pixel(x + w - 2, y + h - 2, C.G2)


def hp_color(cur: int, mx: int) -> int:
    ratio = cur / mx if mx else 0
    if ratio > 0.5:
        return C.LGREEN
    if ratio > 0.25:
        return C.YELLOW
    return C.LRED


def bar(fb: Framebuffer, x: int, y: int, w: int, cur: int, mx: int, color: int, h: int = 3) -> None:
    fb.rect(x - 1, y - 1, w + 2, h + 2, C.BLACK)
    fb.rect(x, y, w, h, C.G4)
    filled = 0 if mx <= 0 else max(1 if cur > 0 else 0, min(w, cur * w // mx))
    if filled:
        fb.rect(x, y, filled, h, color)
        fb.hline(x, y, filled, C.WHITE if h >= 3 else color)


def wrap(text: str, width: int) -> List[str]:
    """Parte un texto en líneas de `width` caracteres como máximo."""
    lines: List[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            candidate = word if not line else line + " " + word
            if len(candidate) <= width:
                line = candidate
            else:
                if line:
                    lines.append(line)
                while len(word) > width:
                    lines.append(word[:width])
                    word = word[width:]
                line = word
        lines.append(line)
    return lines


def draw_member_panel(fb: Framebuffer, m, x: int, y: int, w: int, active: bool = False,
                      hp: Optional[int] = None) -> None:
    """Nombre, nivel, barra de HP y MP de un miembro del grupo (24 px de alto)."""
    hp = m.hp if hp is None else hp
    down = hp <= 0
    name_color = C.G3 if down else (C.YELLOW if active else C.WHITE)
    if active:
        fb.text(x - 7, y, "▶", C.YELLOW)
    fb.text(x, y, m.name[:12], name_color)
    fb.text_right(x + w, y, f"NV{m.level}", C.G1)
    numbers = f"{hp}/{m.max_hp}"
    fb.text(x, y + 9, "HP", C.SKY)
    bar_w = w - 14 - font.ADVANCE * 7 - 2
    bar(fb, x + 14, y + 10, bar_w, hp, m.max_hp, hp_color(hp, m.max_hp), 4)
    fb.text_right(x + w, y + 9, numbers, C.LRED if down else C.WHITE)
    fb.text(x, y + 17, "MP", C.SKY)
    bar(fb, x + 14, y + 18, bar_w, m.mp, m.max_mp, C.CYAN, 3)
    fb.text_right(x + w, y + 17, f"{m.mp}/{m.max_mp}", C.G1)


# --------------------------------------------------------------------- MENÚ
@dataclass
class Choice:
    label: str
    enabled: bool = True
    right: str = ""
    icon: Optional[str] = None


class Menu:
    DENIED = -1

    def __init__(self, x: int, y: int, w: int, choices: Sequence[Choice], rows: Optional[int] = None,
                 row_h: int = 10, digits: bool = False) -> None:
        self.x, self.y, self.w = x, y, w
        self.choices: List[Choice] = list(choices)
        self._auto_rows = rows is None
        self.rows = rows or max(1, len(self.choices))
        self.row_h = row_h
        self.digits = digits
        self.cursor = 0
        self.top = 0

    def set_choices(self, choices: Sequence[Choice]) -> None:
        self.choices = list(choices)
        if self._auto_rows:
            self.rows = max(1, len(self.choices))
        self.cursor = min(self.cursor, max(0, len(self.choices) - 1))
        self._scroll()

    def _scroll(self) -> None:
        if self.cursor < self.top:
            self.top = self.cursor
        elif self.cursor >= self.top + self.rows:
            self.top = self.cursor - self.rows + 1
        self.top = max(0, min(self.top, max(0, len(self.choices) - self.rows)))

    def key(self, key: str, char: str = "") -> Optional[int]:
        """Devuelve el índice elegido, Menu.DENIED si estaba deshabilitado o None."""
        n = len(self.choices)
        if n == 0:
            return None
        if key == "up":
            self.cursor = (self.cursor - 1) % n
            self._scroll()
        elif key == "down":
            self.cursor = (self.cursor + 1) % n
            self._scroll()
        elif key == "confirm":
            return self.cursor if self.choices[self.cursor].enabled else Menu.DENIED
        elif key == "char" and self.digits and char.isdigit():
            idx = int(char) - 1
            if 0 <= idx < n:
                self.cursor = idx
                self._scroll()
                return idx if self.choices[idx].enabled else Menu.DENIED
        return None

    def item_at(self, px: int, py: int) -> Optional[int]:
        if not (self.x <= px < self.x + self.w):
            return None
        row = (py - self.y) // self.row_h
        if 0 <= row < self.rows and py >= self.y and self.top + row < len(self.choices):
            return self.top + row
        return None

    def click(self, px: int, py: int) -> Optional[int]:
        i = self.item_at(px, py)
        if i is None:
            return None
        self.cursor = i
        return i if self.choices[i].enabled else Menu.DENIED

    def motion(self, px: int, py: int) -> bool:
        i = self.item_at(px, py)
        if i is not None and i != self.cursor:
            self.cursor = i
            return True
        return False

    def draw(self, fb: Framebuffer, t: float, active: bool = True) -> None:
        for r in range(self.rows):
            i = self.top + r
            if i >= len(self.choices):
                break
            ch = self.choices[i]
            y = self.y + r * self.row_h
            selected = i == self.cursor
            color = C.G3 if not ch.enabled else (C.YELLOW if selected and active else C.WHITE)
            if selected:
                bob = 1 if (active and int(t * 4) % 2) else 0
                fb.text(self.x + bob, y, "▶", C.WHITE if active else C.G2)
            tx = self.x + 8
            if ch.icon:
                fb.sprite(ICONS[ch.icon], tx, y - 1)
                tx += 10
            fb.text(tx, y, ch.label, color, C.BLACK if ch.enabled else None)
            if ch.right:
                fb.text_right(self.x + self.w, y, ch.right, C.G3 if not ch.enabled else C.GOLD)
        if self.top > 0:
            fb.text_right(self.x + self.w, self.y - 9, "^", C.G1)
        if self.top + self.rows < len(self.choices):
            fb.text_right(self.x + self.w, self.y + self.rows * self.row_h - 2, "v", C.G1)


# ---------------------------------------------------------------- DIÁLOGO
class Dialogue:
    """Cuadro de texto con efecto máquina de escribir. Confirmar avanza."""

    def __init__(self, x: int, y: int, w: int, h: int, cps: float = 70.0) -> None:
        self.x, self.y, self.w, self.h = x, y, w, h
        self.cps = cps
        self.cols = (w - 14) // font.ADVANCE
        self.rows = max(1, (h - 8) // font.LINE_H)
        self.pages: List[List[str]] = []
        self.lines: Optional[List[str]] = None
        self.shown = 0.0
        self.idle_time = 0.0

    # ---- contenido
    def _paginate(self, text: str) -> List[List[str]]:
        lines = wrap(text, self.cols)
        return [lines[i:i + self.rows] for i in range(0, len(lines), self.rows)] or [[""]]

    def say(self, *messages: str) -> None:
        for m in messages:
            self.pages.extend(self._paginate(m))
        if self.lines is None:
            self._load_next()

    def set(self, message: str) -> None:
        """Reemplaza lo que se está mostrando."""
        self.pages = self._paginate(message)
        self._load_next()

    def clear(self) -> None:
        self.pages = []
        self.lines = None

    def _load_next(self) -> None:
        if self.pages:
            self.lines = self.pages.pop(0)
            self.shown = 0.0
            self.idle_time = 0.0
        else:
            self.lines = None

    # ---- estado
    @property
    def active(self) -> bool:
        return self.lines is not None

    @property
    def total_chars(self) -> int:
        return sum(len(line) for line in self.lines) if self.lines else 0

    @property
    def typed(self) -> bool:
        return self.lines is None or self.shown >= self.total_chars

    def update(self, dt: float) -> bool:
        if self.lines is None:
            return False
        if not self.typed:
            self.shown = min(self.total_chars, self.shown + dt * self.cps)
            return True
        self.idle_time += dt
        return False

    def advance(self) -> bool:
        """Confirmar: completa el texto o pasa al siguiente. True si pasó de página."""
        if self.lines is None:
            return True
        if not self.typed:
            self.shown = self.total_chars
            return False
        self._load_next()
        return True

    def draw(self, fb: Framebuffer, t: float) -> None:
        window(fb, self.x, self.y, self.w, self.h)
        if not self.lines:
            return
        remaining = int(self.shown)
        for i, line in enumerate(self.lines):
            part = line[:max(0, remaining)]
            remaining -= len(line)
            fb.text(self.x + 7, self.y + 6 + i * font.LINE_H, part, C.WHITE, C.BLACK)
            if remaining <= 0:
                break
        if self.typed and int(t * 3) % 2 == 0:
            fb.text(self.x + self.w - 12, self.y + self.h - 11, "▶", C.WHITE)
