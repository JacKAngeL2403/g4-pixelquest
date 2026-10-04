"""GameApp: el "cerebro" de la interfaz gráfica.

No sabe nada de Tkinter: recibe teclas/clics/tiempo y dibuja en un Framebuffer.
Por eso se puede probar sin abrir ninguna ventana (ver tests/test_gui.py).
"""
from __future__ import annotations

from typing import List, Optional

from src.domain.models import Hero
from src.services.app_service import GameService

from .framebuffer import Framebuffer
from .screen import Screen


class GameApp:
    def __init__(self, service: GameService) -> None:
        self.service = service
        self.fb = Framebuffer()
        self.hero: Optional[Hero] = None
        self.t = 0.0
        self.dirty = True
        self.should_quit = False
        self.muted = False
        self._sounds: List[str] = []
        self._phase = -1
        self.screen: Screen
        from .screens_menu import TitleScreen
        self.goto(TitleScreen(self))

    # ---- navegación
    def goto(self, screen: Screen) -> None:
        self.screen = screen
        screen.enter()
        self.dirty = True

    # ---- sonido
    def sfx(self, name: str) -> None:
        if not self.muted:
            self._sounds.append(name)

    def pop_sounds(self) -> List[str]:
        sounds, self._sounds = self._sounds, []
        return sounds

    # ---- entrada
    @property
    def wants_text(self) -> bool:
        return self.screen.wants_text

    def key(self, key: str, char: str = "") -> None:
        if key == "char" and char.lower() == "m" and not self.wants_text:
            self.muted = not self.muted
            self.dirty = True
            return
        self.screen.key(key, char)
        self.dirty = True

    def click(self, x: int, y: int, button: int = 1) -> None:
        self.screen.click(x, y, button)
        self.dirty = True

    def motion(self, x: int, y: int) -> None:
        self.screen.motion(x, y)

    # ---- bucle
    def update(self, dt: float) -> bool:
        """Avanza el tiempo. Devuelve True si hay que volver a dibujar."""
        self.t += dt
        changed = self.screen.update(dt) or self.dirty or self.screen.busy
        phase = int(self.t * 8)  # 8 cuadros/s para parpadeos y llamas
        if phase != self._phase:
            self._phase = phase
            changed = True
        self.dirty = False
        return changed

    def render(self) -> Framebuffer:
        self.screen.draw(self.fb)
        return self.fb