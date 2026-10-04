"""Clase base de todas las pantallas del juego."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .framebuffer import Framebuffer
from .widgets import Menu

if TYPE_CHECKING:  # solo para anotaciones
    from .app import GameApp


class Screen:
    wants_text = False   # True si la pantalla lee texto escrito (nombre del héroe)
    busy = False         # True si necesita redibujarse en cada cuadro (animaciones)

    def __init__(self, app: "GameApp") -> None:
        self.app = app

    # ---- ciclo de vida
    def enter(self) -> None:
        """Se llama al mostrarse la pantalla."""

    def update(self, dt: float) -> bool:
        """Avanza animaciones. Devuelve True si hay que redibujar."""
        return False

    def draw(self, fb: Framebuffer) -> None:
        raise NotImplementedError

    # ---- entrada
    def key(self, key: str, char: str = "") -> None:
        """key: up/down/left/right/confirm/cancel/backspace/char."""

    def click(self, x: int, y: int, button: int = 1) -> None:
        """Clic del mouse en coordenadas del juego (0-319, 0-239)."""

    def motion(self, x: int, y: int) -> None:
        """El mouse se movió."""

    # ---- ayudas para menús (con sonido)
    def nav(self, menu: Menu, key: str, char: str = "") -> Optional[int]:
        before = menu.cursor
        result = menu.key(key, char)
        if result == Menu.DENIED:
            self.app.sfx("error")
            return None
        if result is not None:
            self.app.sfx("confirm")
            return result
        if menu.cursor != before:
            self.app.sfx("move")
        return None

    def nav_click(self, menu: Menu, x: int, y: int) -> Optional[int]:
        result = menu.click(x, y)
        if result == Menu.DENIED:
            self.app.sfx("error")
            return None
        if result is not None:
            self.app.sfx("confirm")
        return result

    def nav_motion(self, menu: Menu, x: int, y: int) -> None:
        if menu.motion(x, y):
            self.app.sfx("move")
            self.app.dirty = True