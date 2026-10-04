"""Pantallas de inicio: título, crear héroe y cargar/borrar partida."""
from __future__ import annotations

import math
from typing import List, Optional

from src.domain.exceptions import PixelQuestError

from . import backgrounds as bg
from . import font
from .framebuffer import Framebuffer
from .palette import C
from .screen import Screen
from .sprites import member_sprite
from .widgets import Choice, Dialogue, Menu, window, wrap

PARADE = ["warrior", "mage", "rogue", "cleric", "archer", "knight", "alchemist"]


def _title_logo(fb: Framebuffer, y: int) -> None:
    text = "PIXEL QUEST"
    scale = 4
    x = 160 - fb.text_width(text, scale) // 2
    fb.text(x + 3, y + 3, text, C.BLACK, None, scale)
    fb.text(x + 2, y + 2, text, C.DRED, None, scale)
    fb.text(x, y, text, C.GOLD, None, scale)
    fb.text(x, y - 1, text, C.YELLOW, None, scale)     # brillo superior
    fb.text(x, y, text, C.GOLD, None, scale)
    fb.text_center(160, y + 34, "- UN RPG DE 8 BITS -", C.SKY, C.BLACK)


class TitleScreen(Screen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.menu = Menu(120, 168, 110, [], row_h=12)
        self.dialogue = Dialogue(20, 100, 280, 40)
        self.summaries: List[dict] = []
        self.confirm_quit = False

    def enter(self) -> None:
        self.app.hero = None
        try:
            self.summaries = self.app.service.list_summaries()
        except PixelQuestError as err:
            self.summaries = []
            self.dialogue.say(str(err))
        has = bool(self.summaries)
        self.menu.set_choices([
            Choice("NUEVA PARTIDA"), Choice("CONTINUAR", has),
            Choice("BORRAR PARTIDA", has), Choice("SALIR"),
        ])

    def update(self, dt: float) -> bool:
        return self.dialogue.update(dt)

    def draw(self, fb: Framebuffer) -> None:
        fb.load(bg.title_bg())
        _title_logo(fb, 22)
        t = self.app.t
        for i, key in enumerate(PARADE):
            bob = int(2 * abs(math.sin(t * 3 + i * 0.8)))
            fb.sprite(member_sprite(key), 30 + i * 38, 92 - bob, 2)
        window(fb, 104, 160, 132, 62)
        self.menu.draw(fb, t)
        fb.text_center(160, 229, "FLECHAS + ENTER  /  MOUSE  /  M: SONIDO", C.G2)
        if self.dialogue.active:
            self.dialogue.draw(fb, t)

    def key(self, key: str, char: str = "") -> None:
        if self.dialogue.active:
            if key in ("confirm", "cancel"):
                self.dialogue.advance()
            return
        self._choose(self.nav(self.menu, key, char))

    def click(self, x: int, y: int, button: int = 1) -> None:
        if self.dialogue.active:
            self.dialogue.advance()
        else:
            self._choose(self.nav_click(self.menu, x, y))

    def motion(self, x: int, y: int) -> None:
        if not self.dialogue.active:
            self.nav_motion(self.menu, x, y)

    def _choose(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        if idx == 0:
            self.app.goto(NewHeroScreen(self.app))
        elif idx == 1:
            self.app.goto(LoadScreen(self.app, "load"))
        elif idx == 2:
            self.app.goto(LoadScreen(self.app, "delete"))
        else:
            self.app.should_quit = True


class NewHeroScreen(Screen):
    MAX_LEN = 14

    def __init__(self, app) -> None:
        super().__init__(app)
        self.stage = "name"
        self.name = ""
        self.error = ""
        self.classes = app.service.available_classes()
        self.menu = Menu(20, 50, 112, [Choice(c.CLASS_NAME.upper()) for c in self.classes], row_h=16)

    @property
    def wants_text(self) -> bool:  # type: ignore[override]
        return self.stage == "name"

    def draw(self, fb: Framebuffer) -> None:
        fb.load(bg.camp_bg())
        bg.draw_campfire(fb, 160, 150, self.app.t)
        t = self.app.t
        if self.stage == "name":
            window(fb, 40, 70, 240, 74)
            fb.text_center(160, 80, "¿CÓMO SE LLAMA TU HÉROE?", C.YELLOW, C.BLACK)
            fb.rect(64, 100, 192, 14, C.BLACK)
            fb.outline(64, 100, 192, 14, C.G2)
            caret = "_" if int(t * 3) % 2 == 0 else " "
            fb.text(70, 104, self.name.upper() + caret, C.WHITE)
            fb.text_center(160, 122, "ENTER: SIGUIENTE   ESC: VOLVER", C.G1)
            if self.error:
                fb.text_center(160, 133, self.error, C.LRED)
        else:
            window(fb, 8, 20, 130, 90)
            fb.text(20, 28, "ELIGE TU CLASE", C.YELLOW, C.BLACK)
            self.menu.draw(fb, t)
            cur = self.classes[self.menu.cursor]
            window(fb, 144, 20, 168, 190)
            fb.text_center(228, 28, self.name.upper(), C.WHITE, C.BLACK)
            fb.sprite(member_sprite(cur.CLASS_KEY), 188, 40 - int(2 * abs(math.sin(t * 3))), 5)
            fb.text_center(228, 128, cur.CLASS_NAME.upper(), C.GOLD, C.BLACK)
            rows = [("HP", cur.max_hp, C.LGREEN), ("ATK", cur.attack_power, C.LRED),
                    ("DEF", cur.defense_power, C.SKY), ("MP", cur.max_mp, C.CYAN)]
            for i, (label, value, color) in enumerate(rows):
                fb.text(156, 142 + i * 10, label, C.G1)
                fb.text(190, 142 + i * 10, str(value), color)
                fb.rect(222, 143 + i * 10, min(80, value * 80 // 130), 4, color)
            for i, line in enumerate(wrap("ESPECIAL: " + cur.SPECIAL_NAME.upper(), 26)[:3]):
                fb.text(156, 184 + i * 9, line, C.G1)
            window(fb, 8, 116, 130, 94)
            for i, line in enumerate(wrap("Cada clase tiene una habilidad propia. Luego podrás reclutar "
                                          "compañeros en la taberna.", 19)):
                fb.text(16, 124 + i * 10, line, C.WHITE)
            if self.error:
                fb.text_center(160, 218, self.error, C.LRED, C.BLACK)

    def key(self, key: str, char: str = "") -> None:
        if self.stage == "name":
            if key == "cancel":
                self.app.sfx("cancel")
                self.app.goto(TitleScreen(self.app))
            elif key == "backspace":
                self.name = self.name[:-1]
                self.error = ""
            elif key == "confirm":
                if not self.name.strip():
                    self.error = "ESCRIBE UN NOMBRE"
                    self.app.sfx("error")
                else:
                    self.error = ""
                    self.stage = "class"
                    self.app.sfx("confirm")
            elif key == "char" and len(char) == 1 and len(self.name) < self.MAX_LEN:
                if (char.isalnum() or char == " ") and font.supports(char):
                    self.name += char
                    self.error = ""
                    self.app.sfx("move")
            return
        if key == "cancel":
            self.stage = "name"
            self.app.sfx("cancel")
            return
        self._pick(self.nav(self.menu, key, char))

    def click(self, x: int, y: int, button: int = 1) -> None:
        if self.stage == "class":
            if button == 3:
                self.stage = "name"
            else:
                self._pick(self.nav_click(self.menu, x, y))

    def motion(self, x: int, y: int) -> None:
        if self.stage == "class":
            self.nav_motion(self.menu, x, y)

    def _pick(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        try:
            hero = self.app.service.create_hero(self.name, self.classes[idx].CLASS_KEY)
        except PixelQuestError as err:
            self.error = str(err).upper()[:40]
            self.stage = "name"
            self.app.sfx("error")
            return
        self.app.hero = hero
        from .screens_camp import CampScreen
        self.app.goto(CampScreen(self.app, f"¡{hero.name} el {hero.CLASS_NAME} comienza su aventura! "
                                           "Explora la mazmorra, compra equipo y recluta compañeros."))


class LoadScreen(Screen):
    def __init__(self, app, mode: str) -> None:
        super().__init__(app)
        self.mode = mode  # "load" | "delete"
        self.summaries: List[dict] = []
        self.menu = Menu(20, 46, 170, [], rows=10, row_h=14)
        self.confirm: Optional[Menu] = None
        self.message = ""

    def enter(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        try:
            self.summaries = self.app.service.list_summaries()
        except PixelQuestError as err:
            self.summaries = []
            self.message = str(err)
        self.menu.set_choices([Choice(s["name"].upper(), True, f"NV{s['level']}") for s in self.summaries])
        if not self.summaries:
            self.app.goto(TitleScreen(self.app))

    def draw(self, fb: Framebuffer) -> None:
        fb.load(bg.title_bg())
        t = self.app.t
        window(fb, 8, 8, 196, 214)
        title = "CONTINUAR PARTIDA" if self.mode == "load" else "BORRAR PARTIDA"
        fb.text(20, 20, title, C.YELLOW if self.mode == "load" else C.LRED, C.BLACK)
        self.menu.draw(fb, t, active=self.confirm is None)
        window(fb, 210, 8, 102, 214)
        if self.summaries:
            s = self.summaries[self.menu.cursor]
            fb.sprite(member_sprite(s["class_key"]), 226, 24 - int(2 * abs(math.sin(t * 3))), 4)
            fb.text_center(261, 96, s["name"].upper()[:14], C.WHITE, C.BLACK)
            fb.text_center(261, 108, s["class_name"].upper(), C.GOLD)
            fb.text(220, 128, "NIVEL", C.G1); fb.text_right(304, 128, str(s["level"]), C.WHITE)
            fb.text(220, 140, "PISO", C.G1); fb.text_right(304, 140, str(s["floor"]), C.WHITE)
            fb.text(220, 152, "GRUPO", C.G1); fb.text_right(304, 152, str(1 + s["companions"]), C.WHITE)
        fb.text_center(160, 229, "ENTER: ELEGIR   ESC: VOLVER", C.G2)
        if self.confirm is not None:
            window(fb, 60, 90, 200, 60)
            name = self.summaries[self.menu.cursor]["name"].upper()
            fb.text_center(160, 100, f"¿BORRAR A {name}?", C.LRED, C.BLACK)
            self.confirm.draw(fb, t)
        elif self.message:
            fb.text_center(160, 214, self.message.upper()[:50], C.LRED, C.BLACK)

    def key(self, key: str, char: str = "") -> None:
        if self.confirm is not None:
            if key == "cancel":
                self.confirm = None
                return
            r = self.nav(self.confirm, key, char)
            if r == 0:
                self._delete()
            elif r == 1:
                self.confirm = None
            return
        if key == "cancel":
            self.app.sfx("cancel")
            self.app.goto(TitleScreen(self.app))
            return
        self._pick(self.nav(self.menu, key, char))

    def click(self, x: int, y: int, button: int = 1) -> None:
        if self.confirm is not None:
            r = self.nav_click(self.confirm, x, y)
            if r == 0:
                self._delete()
            elif r == 1:
                self.confirm = None
        elif button == 3:
            self.app.goto(TitleScreen(self.app))
        else:
            self._pick(self.nav_click(self.menu, x, y))

    def motion(self, x: int, y: int) -> None:
        self.nav_motion(self.confirm if self.confirm is not None else self.menu, x, y)

    def _pick(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        name = self.summaries[idx]["name"]
        if self.mode == "delete":
            self.confirm = Menu(120, 116, 80, [Choice("NO"), Choice("SÍ, BORRAR")], row_h=12)
            return
        try:
            self.app.hero = self.app.service.load_hero(name)
        except PixelQuestError as err:
            self.message = str(err)
            self.app.sfx("error")
            return
        from .screens_camp import CampScreen
        self.app.goto(CampScreen(self.app, f"¡Bienvenido de vuelta, {self.app.hero.name}!"))

    def _delete(self) -> None:
        name = self.summaries[self.menu.cursor]["name"]
        try:
            self.app.service.delete_hero(name)
            self.message = "PARTIDA BORRADA"
        except PixelQuestError as err:
            self.message = str(err)
        self.confirm = None
        self._refresh()
