"""Pantalla de combate por turnos en grupo (estilo Final Fantasy)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.domain.exceptions import PixelQuestError
from src.domain.models import Ether, Potion

from . import backgrounds as bg
from .framebuffer import Framebuffer
from .palette import C
from .screen import Screen
from .screens_camp import CampScreen, item_icon
from .sprites import enemy_sprite, member_sprite
from .widgets import Choice, Dialogue, Menu, bar, draw_member_panel, hp_color, window


@dataclass
class Floater:
    """Número flotante (daño / curación)."""
    text: str
    x: int
    y: int
    color: int
    life: float = 0.9
    age: float = 0.0


@dataclass
class Slash:
    x: int
    y: int
    age: float = 0.0
    life: float = 0.3


class CombatScreen(Screen):
    busy = True
    AUTO_DELAY = 0.75

    def __init__(self, app, enemy) -> None:
        super().__init__(app)
        self.enemy = enemy
        self.dialogue = Dialogue(4, 4, 312, 34)
        self.menu = Menu(14, 174, 100, [], row_h=10)
        self.items_menu = Menu(132, 162, 176, [], rows=6, row_h=11)
        self.target_menu = Menu(132, 162, 176, [], row_h=14)
        self.mode = "intro"
        self.queue: List = []
        self.floaters: List[Floater] = []
        self.slashes: List[Slash] = []
        self.flash: Dict[int, float] = {}
        self.shake: Dict[int, float] = {}
        self.dying: Optional[float] = None
        self.enemy_gone = False
        self.timer = 0.0
        self.result_lines: List[str] = []
        self.usable: List[int] = []
        self.pending_item: Optional[int] = None

    # ------------------------------------------------------------------ inicio
    def enter(self) -> None:
        app = self.app
        self.session = app.service.start_combat(app.hero, self.enemy)
        self.shown: Dict[int, int] = {id(m): m.hp for m in self.session.party}
        self.shown[id(self.enemy)] = self.enemy.hp
        if self.enemy.is_boss:
            self.dialogue.set(f"¡{self.enemy.name.upper()} TE DESAFÍA!")
        else:
            self.dialogue.set(f"¡{self.enemy.name.upper()} APARECE!")

    # -------------------------------------------------------------- geometría
    def member_pos(self, i: int):
        return 252 - i * 28, 42 + i * 34

    def enemy_pos(self):
        return (28, 40) if self.enemy.is_boss else (44, 72)

    def enemy_center(self):
        x, y = self.enemy_pos()
        size = 96 if self.enemy.is_boss else 64
        return x + size // 2, y + size // 2

    # ------------------------------------------------------------ comandos
    def _enter_command(self) -> None:
        actor = self.session.current_actor
        if actor is None:
            return
        self.mode = "command"
        usable = [it for it in self.app.hero.inventory.items if isinstance(it, (Potion, Ether))]
        hurt = any(m.is_alive and m.hp < m.max_hp for m in self.session.party)
        can_special = actor.mp >= actor.SPECIAL_COST and (not actor.SPECIAL_ON_ALLY or hurt)
        self.menu.set_choices([
            Choice("ATACAR"),
            Choice(actor.special_short_name.upper()[:14], can_special),
            Choice("DEFENDER"),
            Choice("OBJETO", bool(usable)),
            Choice("HUIR", not self.enemy.is_boss),
        ])
        self.menu.cursor = min(self.menu.cursor, 4)
        self.dialogue.clear()

    def _run(self, fn, *args) -> bool:
        """Ejecuta una acción del combate; devuelve False si fue rechazada."""
        self.shown.update({id(m): self.shown.get(id(m), m.hp) for m in self.session.party})
        try:
            fn(*args)
        except PixelQuestError as err:
            self.app.sfx("error")
            self.dialogue.set(str(err).upper())
            return False
        self.queue = list(self.session.events)
        self.mode = "playback"
        self._next_event()
        return True

    def _next_event(self) -> None:
        if not self.queue:
            self._after_playback()
            return
        ev = self.queue.pop(0)
        self.dialogue.set(ev.text.upper())
        self.timer = 0.0
        self._apply(ev)

    def _apply(self, ev) -> None:
        tgt = ev.target
        if tgt is None:
            return
        tid = id(tgt)
        is_enemy = tgt is self.enemy
        cx, cy = self.enemy_center() if is_enemy else self._member_center(tgt)
        if ev.kind == "hit":
            self.shown[tid] = max(0, self.shown.get(tid, tgt.hp) - ev.amount)
            self.flash[tid] = 0.2
            self.shake[tid] = 0.3
            self.floaters.append(Floater(str(ev.amount), cx - 6, cy - 10, C.WHITE))
            if is_enemy:
                self.slashes.append(Slash(cx, cy))
                self.app.sfx("hit")
                if self.shown[tid] == 0:
                    self.dying = 0.7
            else:
                self.app.sfx("hurt")
        elif ev.kind == "heal":
            self.shown[tid] = min(tgt.max_hp, self.shown.get(tid, tgt.hp) + ev.amount)
            if ev.amount:
                self.floaters.append(Floater(f"+{ev.amount}", cx - 10, cy - 10, C.LGREEN))
            self.flash[tid] = 0.0
            self.app.sfx("heal")

    def _member_center(self, member):
        i = self.session.party.index(member)
        x, y = self.member_pos(i)
        return x + 24, y + 24

    def _after_playback(self) -> None:
        if self.session.is_over:
            self.result_lines = self.app.service.finish_combat(self.session)
            self.app.sfx("win" if self.session.victory else ("lose" if not self.session.fled else "cancel"))
            if any("SUBE A NIVEL" in l for l in self.result_lines):
                self.app.sfx("levelup")
            self.mode = "result"
            self.dialogue.set(self.result_lines[0].upper())
            self.dialogue.say(*[l.upper() for l in self.result_lines[1:]])
        else:
            self._enter_command()

    # ------------------------------------------------------------- tiempo
    def update(self, dt: float) -> bool:
        self.timer += dt
        self.dialogue.update(dt)
        for d in (self.flash, self.shake):
            for k in list(d):
                d[k] -= dt
                if d[k] <= 0:
                    del d[k]
        for f in self.floaters:
            f.age += dt
        self.floaters = [f for f in self.floaters if f.age < f.life]
        for s in self.slashes:
            s.age += dt
        self.slashes = [s for s in self.slashes if s.age < s.life]
        if self.dying is not None:
            self.dying -= dt
            if self.dying <= 0:
                self.dying = None
                self.enemy_gone = True
        if self.mode == "intro" and self.timer > 1.3:
            self._enter_command()
        elif self.mode == "playback" and self.dialogue.typed and self.timer > self.AUTO_DELAY:
            self._next_event()
        return True

    # ------------------------------------------------------------- dibujo
    def draw(self, fb: Framebuffer) -> None:
        hero, t = self.app.hero, self.app.t
        fb.load(bg.dungeon_bg(hero.floor))
        bg.draw_torches(fb, t)
        self._draw_enemy(fb)
        self._draw_party(fb)
        for s in self.slashes:
            p = s.age / s.life
            for k in range(3):
                off = k * 7 - 7
                fb.line(s.x - 20 + off, s.y - 22, s.x + 18 + off - int(p * 6), s.y + 22, C.WHITE if k == 1 else C.YELLOW)
        for f in self.floaters:
            y = f.y - int(f.age * 26)
            fb.text(f.x, y, f.text, f.color, C.BLACK, 2)
        # panel inferior
        window(fb, 4, 154, 120, 82)
        window(fb, 128, 154, 188, 82)
        if self.mode == "command":
            actor = self.session.current_actor
            fb.text(14, 160, f"TURNO: {actor.name.upper()[:10]}", C.YELLOW, C.BLACK)
            self.menu.draw(fb, t)
            sel = self.menu.cursor
            if sel == 1:
                fb.text(14, 226, f"COSTE {actor.SPECIAL_COST} MP", C.CYAN)
        else:
            fb.text(14, 160, self.enemy.name.upper()[:14], C.YELLOW, C.BLACK)
            ehp = self.shown.get(id(self.enemy), self.enemy.hp)
            bar(fb, 14, 178, 100, ehp, self.enemy.max_hp, hp_color(ehp, self.enemy.max_hp), 5)
            fb.text(14, 188, f"HP {ehp}/{self.enemy.max_hp}", C.WHITE)
            if getattr(self.enemy, "enraged", False) and ehp > 0:
                fb.text(14, 200, "¡FURIOSO!", C.LRED)
        if self.mode == "item":
            self.items_menu.draw(fb, t)
            fb.text(134, 156, "OBJETO  (ESC: VOLVER)", C.SKY)
        elif self.mode == "target":
            fb.text(134, 156, "¿SOBRE QUIÉN?  (ESC: VOLVER)", C.SKY)
            self.target_menu.draw(fb, t)
        else:
            actor = self.session.current_actor if self.mode == "command" else None
            for i, m in enumerate(self.session.party):
                draw_member_panel(fb, m, 144, 159 + i * 26, 164, active=m is actor,
                                  hp=self.shown.get(id(m), m.hp))
        if self.dialogue.active or self.mode in ("intro", "playback", "result"):
            self.dialogue.draw(fb, t)

    def _draw_enemy(self, fb: Framebuffer) -> None:
        if self.enemy_gone:
            return
        spr, scale = enemy_sprite(self.enemy.name, self.enemy.is_boss)
        x, y = self.enemy_pos()
        tid = id(self.enemy)
        if tid in self.shake:
            x += int(3 * math.sin(self.shake[tid] * 50))
        y += int(2 * math.sin(self.app.t * 2.5))
        if self.dying is not None and int(self.dying * 20) % 2:
            return
        tint = C.WHITE if tid in self.flash else None
        fb.sprite(spr, x, y, scale, tint=tint)

    def _draw_party(self, fb: Framebuffer) -> None:
        actor = self.session.current_actor if self.mode == "command" else None
        for i in reversed(range(len(self.session.party))):
            m = self.session.party[i]
            x, y = self.member_pos(i)
            down = self.shown.get(id(m), m.hp) <= 0
            if m is actor:
                x -= 10
            if id(m) in self.shake:
                x += int(3 * math.sin(self.shake[id(m)] * 50))
            bob = 0 if down else int(abs(math.sin(self.app.t * 2 + i)))
            tint = C.WHITE if id(m) in self.flash else (C.G3 if down else None)
            fb.sprite(member_sprite(m.CLASS_KEY), x, y - bob, 3, tint=tint)
            if m is actor:
                fb.text(x + 18, y - 6, "v", C.YELLOW, C.BLACK)

    # ------------------------------------------------------------- entrada
    def key(self, key: str, char: str = "") -> None:
        if self.mode in ("intro", "playback", "result"):
            if key in ("confirm", "cancel"):
                self._skip()
            return
        if self.mode == "command":
            self._command(self.nav(self.menu, key, char))
            if self.dialogue.active and key in ("confirm",):
                pass
        elif self.mode == "item":
            if key == "cancel":
                self.mode = "command"
                self.app.sfx("cancel")
            else:
                self._pick_item(self.nav(self.items_menu, key, char))
        elif self.mode == "target":
            if key == "cancel":
                self.mode = "item"
                self.app.sfx("cancel")
            else:
                self._use_on(self.nav(self.target_menu, key, char))

    def click(self, x: int, y: int, button: int = 1) -> None:
        if self.mode in ("intro", "playback", "result"):
            self._skip()
        elif button == 3:
            self.key("cancel")
        elif self.mode == "command":
            self._command(self.nav_click(self.menu, x, y))
        elif self.mode == "item":
            self._pick_item(self.nav_click(self.items_menu, x, y))
        elif self.mode == "target":
            self._use_on(self.nav_click(self.target_menu, x, y))

    def motion(self, x: int, y: int) -> None:
        menu = {"command": self.menu, "item": self.items_menu, "target": self.target_menu}.get(self.mode)
        if menu is not None:
            self.nav_motion(menu, x, y)

    def _skip(self) -> None:
        if self.mode == "intro":
            self._enter_command()
        elif self.mode == "playback":
            if not self.dialogue.typed:
                self.dialogue.advance()
            else:
                self._next_event()
        elif self.mode == "result":
            self.dialogue.advance()
            if not self.dialogue.active:
                self.app.goto(CampScreen(self.app))

    def _command(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        s = self.session
        if idx == 0:
            self._run(s.player_attack)
        elif idx == 1:
            self._run(s.player_special)
        elif idx == 2:
            self._run(s.player_defend)
        elif idx == 3:
            items = self.app.hero.inventory.items
            self.usable = [i for i, it in enumerate(items) if isinstance(it, (Potion, Ether))]
            self.items_menu.set_choices([
                Choice(items[i].name.upper()[:17], True, "", item_icon(items[i])) for i in self.usable])
            self.items_menu.cursor = 0
            self.mode = "item"
        else:
            self._run(s.player_flee)

    def _pick_item(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        self.pending_item = self.usable[idx]
        party = self.session.party
        self.target_menu.set_choices([
            Choice(m.name.upper()[:9], True, f"{m.hp}/{m.max_hp}") for m in party])
        self.target_menu.cursor = self.session.party.index(self.session.current_actor)
        self.mode = "target"

    def _use_on(self, idx: Optional[int]) -> None:
        if idx is None or self.pending_item is None:
            return
        if not self._run(self.session.player_use_item, self.pending_item, idx):
            self.mode = "command"
