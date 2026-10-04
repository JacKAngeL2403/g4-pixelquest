"""Framebuffer de 320x240 píxeles con paleta indexada + exportación a PNG.

Es el "monitor" del juego: las pantallas dibujan aquí con rect(), sprite() y
text(); la ventana (Tkinter) o un test solo tienen que llamar a png().
"""
from __future__ import annotations

import struct
import zlib
from typing import Dict, List, Optional, Sequence, Tuple

from . import font
from .palette import C, LEGEND, NAMES, TABLE_B, TABLE_G, TABLE_R, TRANSPARENT

W, H = 320, 240


class Sprite:
    """Imagen de píxeles indexados. Se crea desde filas de texto (ver LEGEND)."""

    def __init__(self, rows: Sequence[str]) -> None:
        self.h = len(rows)
        self.w = max(len(r) for r in rows)
        self.pixels: List[bytearray] = []
        for r in rows:
            r = r.ljust(self.w, ".")
            self.pixels.append(bytearray(
                TRANSPARENT if ch == "." else getattr(C, LEGEND[ch]) for ch in r))
        self._cache: Dict[Tuple[int, bool, Optional[int]], List[bytes]] = {}

    def swapped(self, mapping: Dict[str, str]) -> "Sprite":
        """Copia con colores cambiados: {'g': 'r'} cambia el verde por rojo."""
        table = {getattr(C, LEGEND[a]): getattr(C, LEGEND[b]) for a, b in mapping.items()}
        new = Sprite(["." * self.w] * self.h)
        new.pixels = [bytearray(table.get(p, p) for p in row) for row in self.pixels]
        return new

    def rows(self, scale: int, flip: bool, tint: Optional[int]) -> List[bytes]:
        key = (scale, flip, tint)
        if key not in self._cache:
            out: List[bytes] = []
            for row in self.pixels:
                r = bytes(row[::-1]) if flip else bytes(row)
                if tint is not None:
                    r = bytes(TRANSPARENT if p == TRANSPARENT else tint for p in r)
                if scale > 1:
                    wide = bytearray()
                    for p in r:
                        wide += bytes([p]) * scale
                    r = bytes(wide)
                out.extend([r] * scale)
            self._cache[key] = out
        return self._cache[key]


class Framebuffer:
    def __init__(self) -> None:
        self.px = bytearray(W * H)

    # ------------------------------------------------------------ básicos
    def clear(self, color: int = C.BLACK) -> None:
        self.px[:] = bytes([color]) * (W * H)

    def load(self, data: bytes) -> None:
        self.px[:] = data

    def snapshot(self) -> bytes:
        return bytes(self.px)

    def pixel(self, x: int, y: int, c: int) -> None:
        if 0 <= x < W and 0 <= y < H:
            self.px[y * W + x] = c

    def rect(self, x: int, y: int, w: int, h: int, c: int) -> None:
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes([c]) * (x1 - x0)
        for yy in range(y0, y1):
            off = yy * W + x0
            self.px[off:off + (x1 - x0)] = row

    def hline(self, x: int, y: int, w: int, c: int) -> None:
        self.rect(x, y, w, 1, c)

    def vline(self, x: int, y: int, h: int, c: int) -> None:
        self.rect(x, y, 1, h, c)

    def outline(self, x: int, y: int, w: int, h: int, c: int) -> None:
        self.hline(x, y, w, c)
        self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c)
        self.vline(x + w - 1, y, h, c)

    def gradient(self, x: int, y: int, w: int, h: int, colors: Sequence[int]) -> None:
        """Bandas horizontales de colores (de arriba hacia abajo)."""
        n = len(colors)
        for i, c in enumerate(colors):
            y0 = y + h * i // n
            y1 = y + h * (i + 1) // n
            self.rect(x, y0, w, y1 - y0, c)

    def ellipse(self, cx: int, cy: int, rx: int, ry: int, c: int) -> None:
        for dy in range(-ry, ry + 1):
            span = int(rx * (1 - (dy / (ry + 0.5)) ** 2) ** 0.5 + 0.5)
            self.rect(cx - span, cy + dy, span * 2 + 1, 1, c)

    def line(self, x0: int, y0: int, x1: int, y1: int, c: int) -> None:
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.pixel(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    # ------------------------------------------------------------ sprites
    def sprite(self, spr: Sprite, x: int, y: int, scale: int = 1, flip: bool = False,
               tint: Optional[int] = None) -> None:
        rows = spr.rows(scale, flip, tint)
        width = spr.w * scale
        for j, row in enumerate(rows):
            yy = y + j
            if yy < 0 or yy >= H:
                continue
            x0 = max(0, -x)
            x1 = min(width, W - x)
            if x1 <= x0:
                continue
            base = yy * W + x
            px = self.px
            for i in range(x0, x1):
                p = row[i]
                if p != TRANSPARENT:
                    px[base + i] = p

    # -------------------------------------------------------------- texto
    @staticmethod
    def text_width(s: str, scale: int = 1) -> int:
        return max(0, len(s) * font.ADVANCE - 1) * scale

    def text(self, x: int, y: int, s: str, color: int = C.WHITE, shadow: Optional[int] = None,
             scale: int = 1) -> int:
        """Dibuja texto (mayúsculas). Devuelve el ancho dibujado."""
        if shadow is not None:
            self.text(x + scale, y + scale, s, shadow, None, scale)
        cx = x
        for ch in s:
            for gx, gy in font.glyph(ch):
                if scale == 1:
                    self.pixel(cx + gx, y + gy, color)
                else:
                    self.rect(cx + gx * scale, y + gy * scale, scale, scale, color)
            cx += font.ADVANCE * scale
        return cx - x

    def text_right(self, right: int, y: int, s: str, color: int = C.WHITE,
                   shadow: Optional[int] = None) -> None:
        self.text(right - self.text_width(s), y, s, color, shadow)

    def text_center(self, cx: int, y: int, s: str, color: int = C.WHITE,
                    shadow: Optional[int] = None, scale: int = 1) -> None:
        self.text(cx - self.text_width(s, scale) // 2, y, s, color, shadow, scale)

    # ---------------------------------------------------------- exportar
    def rgb(self, scale: int = 1) -> bytes:
        """Imagen RGB (3 bytes por píxel) ampliada `scale` veces (vecino más cercano)."""
        src = bytes(self.px)
        chans = (src.translate(TABLE_R), src.translate(TABLE_G), src.translate(TABLE_B))
        if scale == 1:
            out = bytearray(W * H * 3)
            for i, ch in enumerate(chans):
                out[i::3] = ch
            return bytes(out)
        wide = bytearray(W * H * scale * 3)
        for k in range(scale):
            for i, ch in enumerate(chans):
                wide[k * 3 + i::3 * scale] = ch
        rowlen = W * scale * 3
        out = bytearray()
        for y in range(H):
            out += bytes(wide[y * rowlen:(y + 1) * rowlen]) * scale
        return bytes(out)

    def png(self, scale: int = 1) -> bytes:
        rgb = self.rgb(scale)
        w, h = W * scale, H * scale
        rowlen = w * 3
        raw = bytearray()
        for y in range(h):
            raw.append(0)  # filtro "ninguno"
            raw += rgb[y * rowlen:(y + 1) * rowlen]

        def chunk(tag: bytes, data: bytes) -> bytes:
            body = tag + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 1))
                + chunk(b"IEND", b""))
