"""Pantallas del campamento: hub, exploración, inventario, tienda, taberna y estado."""
from __future__ import annotations

import math
from typing import List, Optional

from src.domain.exceptions import PixelQuestError
from src.domain.models import Accessory, Armor, Ether, Potion, Weapon
from src.services.app_service import ROOMS_PER_FLOOR, next_unlock_floor

from . import backgrounds as bg
from .framebuffer import Framebuffer
from .palette import C
from .screen import Screen
from .sprites import ICONS, enemy_sprite, member_sprite, scene_sprite
from .widgets import Choice, Dialogue, Menu, bar, draw_member_panel, hp_color, window, wrap


def item_icon(item) -> str:
    if isinstance(item, Weapon):
        return "weapon"
    if isinstance(item, Armor):
        return "armor"
    if isinstance(item, Potion):
        return "potion"
    if isinstance(item, Ether):
        return "ether"
    return "accessory"


def top_bar(fb: Framebuffer, hero, left: str) -> None:
    window(fb, 4, 4, 312, 18)
    fb.text(12, 9, left, C.WHITE, C.BLACK)
    fb.sprite(ICONS["coin"], 262, 8)
    fb.text_right(308, 9, f"{hero.gold}", C.GOLD, C.BLACK)


def _stone_bg(fb: Framebuffer) -> None:
    fb.load(bg.dungeon_bg(5))


# ------------------------------------------------------------------ CAMPAMENTO
class CampScreen(Screen):
    def __init__(self, app, message: str = "") -> None:
        super().__init__(app)
        self.menu = Menu(16, 160, 96, [], rows=8, row_h=9)
        self.dialogue = Dialogue(30, 30, 260, 46)
        self._message = message

    def enter(self) -> None:
        hero = self.app.hero
        self.menu.set_choices([
            Choice("EXPLORAR"), Choice("INVENTARIO"), Choice("TIENDA"), Choice("TABERNA"),
            Choice(f"POSADA {self.app.service.inn_price(hero)}"), Choice("ESTADO"),
            Choice("GUARDAR"), Choice("SALIR"),
        ])
        if self._message:
            self.dialogue.say(self._message)
            self._message = ""

    def update(self, dt: float) -> bool:
        return self.dialogue.update(dt)

    def draw(self, fb: Framebuffer) -> None:
        hero, t = self.app.hero, self.app.t
        fb.load(bg.camp_bg())
        bg.draw_campfire(fb, 190, 138, t)
        for i, m in enumerate(hero.party):
            bob = int(abs(math.sin(t * 2 + i))) if m.is_alive else 0
            fb.sprite(member_sprite(m.CLASS_KEY), 36 + i * 40, 98 - bob, 3,
                      tint=None if m.is_alive else C.G3)
        top_bar(fb, hero, f"PISO {hero.floor}   SALA {hero.rooms_in_floor}/{ROOMS_PER_FLOOR}")
        window(fb, 4, 154, 112, 82)
        self.menu.draw(fb, t, active=not self.dialogue.active)
        window(fb, 120, 154, 196, 82)
        for i, m in enumerate(hero.party):
            draw_member_panel(fb, m, 136, 159 + i * 26, 172)
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
        app, hero = self.app, self.app.hero
        if idx == 0:
            app.goto(ExploreScreen(app))
        elif idx == 1:
            app.goto(InventoryScreen(app))
        elif idx == 2:
            app.goto(ShopScreen(app))
        elif idx == 3:
            app.goto(TavernScreen(app))
        elif idx == 4:
            try:
                self.dialogue.say(app.service.rest(hero))
                app.sfx("heal")
            except PixelQuestError as err:
                self.dialogue.say(str(err))
                app.sfx("error")
        elif idx == 5:
            app.goto(StatusScreen(app))
        elif idx == 6:
            try:
                app.service.save_hero(hero)
                self.dialogue.say("Partida guardada.")
            except PixelQuestError as err:
                self.dialogue.say(str(err))
        else:
            try:
                app.service.save_hero(hero)
            except PixelQuestError:
                pass
            from .screens_menu import TitleScreen
            app.goto(TitleScreen(app))


# ------------------------------------------------------------------ EXPLORAR
class ExploreScreen(Screen):
    busy = True
    WALK_TIME = 1.1

    def __init__(self, app) -> None:
        super().__init__(app)
        self.dialogue = Dialogue(4, 176, 312, 58)
        self.timer = 0.0
        self.phase = "walk"
        self._last_step = -1

    def enter(self) -> None:
        hero = self.app.hero
        self.event = self.app.service.explore(hero)
        if self.event.enemy is None:
            try:
                self.app.service.save_hero(hero)
            except PixelQuestError:
                pass

    def update(self, dt: float) -> bool:
        self.timer += dt
        if self.phase == "walk":
            step = int(self.timer * 6)
            if step != self._last_step:
                self._last_step = step
                self.app.sfx("step")
            if self.timer >= self.WALK_TIME:
                self.phase, self.timer = "event", 0.0
                self.dialogue.say(self.event.message)
                self.app.sfx({"combat": "alert", "boss": "alert", "treasure": "coin",
                              "fountain": "heal", "trap": "hurt"}.get(self.event.kind, "confirm"))
        elif self.phase == "event":
            self.dialogue.update(dt)
        elif self.phase == "wipe" and self.timer >= 0.7:
            from .screens_combat import CombatScreen
            self.app.goto(CombatScreen(self.app, self.event.enemy))
        return True

    def draw(self, fb: Framebuffer) -> None:
        hero, t = self.app.hero, self.app.t
        fb.load(bg.dungeon_bg(hero.floor))
        bg.draw_torches(fb, t)
        top_bar(fb, hero, f"PISO {hero.floor}   SALA {hero.rooms_in_floor}/{ROOMS_PER_FLOOR}")
        p = min(1.0, self.timer / self.WALK_TIME) if self.phase == "walk" else 1.0
        eased = 1 - (1 - p) ** 2
        kind = self.event.kind
        if self.phase != "walk" or p > 0.55:
            if kind in ("combat", "boss") and self.event.enemy is not None:
                spr, scale = enemy_sprite(self.event.enemy.name, self.event.enemy.is_boss)
                fb.sprite(spr, 200 if scale == 4 else 196, 52 if scale == 4 else 28, scale, tint=C.STONE4)
            elif kind == "treasure":
                fb.sprite(scene_sprite("chest"), 232, 84, 3)
                if int(t * 4) % 2:
                    fb.text(258, 80, "+", C.YELLOW)
            elif kind == "fountain":
                fb.sprite(scene_sprite("fountain"), 232, 82, 3)
            elif kind == "trap":
                fb.sprite(scene_sprite("spikes"), 232, 100, 3)
        for i in reversed(range(len(hero.party))):
            m = hero.party[i]
            x = int(150 - i * 38 - (1 - eased) * 300)
            bob = int(2 * abs(math.sin(self.timer * 12))) if self.phase == "walk" and p < 1 else 0
            fb.sprite(member_sprite(m.CLASS_KEY), x, 80 - bob, 3, tint=None if m.is_alive else C.G3)
        if self.phase == "event" and kind in ("combat", "boss") and int(t * 4) % 2 == 0:
            fb.text(168, 56, "!", C.YELLOW, C.BLACK, 3)
        if self.phase == "wipe":
            h = int(min(1.0, self.timer / 0.6) * 120)
            fb.rect(0, 0, 320, h, C.BLACK)
            fb.rect(0, 240 - h, 320, h, C.BLACK)
        if self.phase in ("event",) or self.dialogue.active:
            self.dialogue.draw(fb, t)

    def _finish(self) -> None:
        if self.event.enemy is not None:
            self.phase, self.timer = "wipe", 0.0
        else:
            self.app.goto(CampScreen(self.app))

    def key(self, key: str, char: str = "") -> None:
        if self.phase != "event" or key not in ("confirm", "cancel"):
            return
        self.dialogue.advance()
        if not self.dialogue.active:
            self._finish()

    def click(self, x: int, y: int, button: int = 1) -> None:
        self.key("confirm")


# ------------------------------------------------------------------ INVENTARIO
class InventoryScreen(Screen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.list = Menu(14, 34, 160, [], rows=13, row_h=10)
        self.actions = Menu(98, 60, 70, [], row_h=10)
        self.targets = Menu(110, 50, 190, [], row_h=12)
        self.codes: List[str] = []
        self.state = "list"
        self.msg = ""
        self.msg_err = False
        self._rebuild()

    def _rebuild(self) -> None:
        items = self.app.hero.inventory.items
        self.list.set_choices([Choice(it.name.upper(), True, "", item_icon(it)) for it in items])

    def _selected(self):
        items = self.app.hero.inventory.items
        return items[self.list.cursor] if items else None

    def draw(self, fb: Framebuffer) -> None:
        hero, t = self.app.hero, self.app.t
        _stone_bg(fb)
        inv = hero.inventory
        top_bar(fb, hero, f"MOCHILA  {len(inv)}/{inv.capacity}")
        window(fb, 4, 26, 176, 150)
        if not len(inv):
            fb.text_center(92, 90, "(VACIA)", C.G2)
        self.list.draw(fb, t, active=self.state == "list")
        window(fb, 184, 26, 132, 150)
        item = self._selected()
        if item:
            y = 34
            for line in wrap(item.name.upper(), 19):
                fb.text(192, y, line, C.YELLOW, C.BLACK)
                y += 10
            for line in wrap(item.describe().upper(), 19):
                fb.text(192, y, line, C.WHITE)
                y += 10
            for line in wrap(item.description.upper(), 19)[:2]:
                fb.text(192, y, line, C.G1)
                y += 10
            fb.text(192, y + 2, f"VALOR {item.value} ORO", C.GOLD)
        fb.hline(190, 108, 120, C.G2)
        fb.text(192, 112, "EQUIPO DE " + hero.name.upper()[:8], C.SKY)
        for i, (label, eq) in enumerate((("ARMA", hero.weapon), ("ARMADURA", hero.armor),
                                         ("ACCESORIO", hero.accessory))):
            fb.text(192, 124 + i * 16, label, C.G1)
            fb.text(198, 133 + i * 16, eq.name.upper()[:18] if eq else "-", C.WHITE if eq else C.G3)
        window(fb, 4, 180, 312, 56)
        if self.msg:
            for i, line in enumerate(wrap(self.msg.upper(), 50)[:4]):
                fb.text(12, 188 + i * 10, line, C.LRED if self.msg_err else C.LGREEN, C.BLACK)
        else:
            for i, m in enumerate(hero.party):
                bx = 12 + i * 102
                fb.text(bx, 188, m.name.upper()[:9], C.WHITE)
                bar(fb, bx, 200, 90, m.hp, m.max_hp, hp_color(m.hp, m.max_hp), 4)
                fb.text(bx, 207, f"{m.hp}/{m.max_hp}", C.G1)
                bar(fb, bx, 220, 90, m.mp, m.max_mp, C.CYAN, 3)
            fb.text_right(306, 228, "ENTER: ELEGIR  ESC: VOLVER", C.G2)
        if self.state == "actions":
            window(fb, 92, 52, 84, 12 + 10 * len(self.codes))
            self.actions.draw(fb, t)
        elif self.state == "target":
            window(fb, 100, 42, 208, 16 + 12 * len(self.targets.choices))
            fb.text(110, 46, "¿SOBRE QUIÉN?", C.YELLOW, C.BLACK)
            self.targets.draw(fb, t)

    # ---- entrada
    def key(self, key: str, char: str = "") -> None:
        if key != "char":
            self.msg = ""
        if self.state == "list":
            if key == "cancel":
                self.app.sfx("cancel")
                self.app.goto(CampScreen(self.app))
            else:
                self._open_actions(self.nav(self.list, key, char))
        elif self.state == "actions":
            if key == "cancel":
                self.state = "list"
            else:
                self._do_action(self.nav(self.actions, key, char))
        elif self.state == "target":
            if key == "cancel":
                self.state = "list"
            else:
                self._do_target(self.nav(self.targets, key, char))

    def click(self, x: int, y: int, button: int = 1) -> None:
        if button == 3:
            self.key("cancel")
            return
        self.msg = ""
        if self.state == "list":
            self._open_actions(self.nav_click(self.list, x, y))
        elif self.state == "actions":
            self._do_action(self.nav_click(self.actions, x, y))
        else:
            self._do_target(self.nav_click(self.targets, x, y))

    def motion(self, x: int, y: int) -> None:
        menu = {"list": self.list, "actions": self.actions, "target": self.targets}[self.state]
        self.nav_motion(menu, x, y)

    def _open_actions(self, idx: Optional[int]) -> None:
        item = self._selected()
        if idx is None or item is None:
            return
        self.codes = []
        if isinstance(item, (Potion, Ether)):
            self.codes.append("use")
        if isinstance(item, (Weapon, Armor, Accessory)):
            self.codes.append("equip")
        self.codes += ["drop", "cancel"]
        names = {"use": "USAR", "equip": "EQUIPAR", "drop": "TIRAR", "cancel": "VOLVER"}
        self.actions.set_choices([Choice(names[c]) for c in self.codes])
        self.actions.cursor = 0
        self.state = "actions"

    def _do_action(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        code, hero, svc = self.codes[idx], self.app.hero, self.app.service
        pos = self.list.cursor
        if code == "cancel":
            self.state = "list"
        elif code == "use":
            self.targets.set_choices([
                Choice(m.name.upper()[:9], True, f"{m.hp}/{m.max_hp}") for m in hero.party])
            self.targets.cursor = 0
            self.state = "target"
        else:
            try:
                self.msg = svc.equip(hero, pos) if code == "equip" else svc.drop_item(hero, pos)
                self.msg_err = False
            except PixelQuestError as err:
                self.msg, self.msg_err = str(err), True
                self.app.sfx("error")
            self.state = "list"
            self._rebuild()

    def _do_target(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        try:
            self.msg = self.app.service.use_item(self.app.hero, self.list.cursor, idx)
            self.msg_err = False
            self.app.sfx("heal")
        except PixelQuestError as err:
            self.msg, self.msg_err = str(err), True
            self.app.sfx("error")
        self.state = "list"
        self._rebuild()


# ---------------------------------------------------------------------- TIENDA
class ShopScreen(Screen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.tabs = Menu(14, 34, 70, [Choice("COMPRAR"), Choice("VENDER"), Choice("SALIR")], row_h=12)
        self.list = Menu(104, 34, 202, [], rows=12, row_h=10)
        self.focus = "tabs"
        self.msg = ""
        self.msg_err = False
        self._items: list = []
        self._rebuild()

    @property
    def mode(self) -> str:
        return "sell" if self.tabs.cursor == 1 else "buy"

    def _rebuild(self) -> None:
        hero, svc = self.app.hero, self.app.service
        if self.mode == "buy":
            self._items = svc.shop_items(hero)
            choices = [Choice(it.name.upper(), hero.gold >= it.value, str(it.value), item_icon(it))
                       for it in self._items]
        else:
            self._items = hero.inventory.items
            choices = [Choice(it.name.upper(), True, str(svc.sell_price(it)), item_icon(it))
                       for it in self._items]
        self.list.set_choices(choices)

    def _compare(self, item) -> List[tuple]:
        hero = self.app.hero
        rows = []
        if isinstance(item, Weapon):
            cur = hero.weapon.attack_bonus if hero.weapon else 0
            rows.append(("ATK", item.attack_bonus - cur))
        elif isinstance(item, Armor):
            cur = hero.armor.defense_bonus if hero.armor else 0
            rows.append(("DEF", item.defense_bonus - cur))
        elif isinstance(item, Accessory):
            cur = hero.accessory
            rows.append(("ATK", item.attack_bonus - (cur.attack_bonus if cur else 0)))
            rows.append(("DEF", item.defense_bonus - (cur.defense_bonus if cur else 0)))
        return rows

    def draw(self, fb: Framebuffer) -> None:
        hero, t = self.app.hero, self.app.t
        _stone_bg(fb)
        top_bar(fb, hero, "TIENDA DEL PUEBLO")
        window(fb, 4, 26, 90, 54)
        self.tabs.draw(fb, t, active=self.focus == "tabs")
        window(fb, 4, 84, 90, 92)
        fb.sprite(member_sprite("alchemist"), 30, 88, 2)
        fb.text(10, 124, f"MOCHILA {len(hero.inventory)}/{hero.inventory.capacity}", C.G1)
        unlock = next_unlock_floor(hero.floor)
        note = f"NUEVOS PRODUCTOS EN EL PISO {unlock}" if unlock else "¡TIENES TODO EL CATALOGO!"
        for i, line in enumerate(wrap(note, 14)[:4]):
            fb.text(10, 138 + i * 9, line, C.SKY)
        window(fb, 98, 26, 218, 150)
        if not self._items:
            fb.text_center(207, 90, "(NADA QUE MOSTRAR)", C.G2)
        self.list.draw(fb, t, active=self.focus == "list")
        window(fb, 4, 180, 312, 56)
        item = self._items[self.list.cursor] if self._items else None
        if item:
            fb.text(12, 186, item.name.upper(), C.YELLOW, C.BLACK)
            fb.text(12, 196, item.describe().upper(), C.WHITE)
            fb.text(12, 206, item.description.upper(), C.G1)
            x = 200
            for label, diff in self._compare(item):
                col = C.LGREEN if diff > 0 else (C.LRED if diff < 0 else C.G1)
                fb.text(x, 196, f"{label} {diff:+d}", col)
                x += 54
        if self.msg:
            fb.text(12, 220, self.msg.upper()[:52], C.LRED if self.msg_err else C.LGREEN, C.BLACK)
        else:
            fb.text(12, 220, "ENTER: ELEGIR   ESC: ATRAS", C.G2)

    def key(self, key: str, char: str = "") -> None:
        if key != "char":
            self.msg = ""
        if self.focus == "tabs":
            if key == "cancel":
                self.app.sfx("cancel")
                self.app.goto(CampScreen(self.app))
                return
            before = self.tabs.cursor
            idx = self.nav(self.tabs, key, char)
            if self.tabs.cursor != before:
                self.list.cursor = 0
                self.list.top = 0
                self._rebuild()
            self._tab_chosen(idx)
        else:
            if key == "cancel":
                self.focus = "tabs"
                self.app.sfx("cancel")
            else:
                self._act(self.nav(self.list, key, char))

    def click(self, x: int, y: int, button: int = 1) -> None:
        if button == 3:
            self.key("cancel")
            return
        self.msg = ""
        if self.focus == "tabs":
            before = self.tabs.cursor
            idx = self.nav_click(self.tabs, x, y)
            if self.tabs.cursor != before:
                self.list.cursor = self.list.top = 0
                self._rebuild()
            self._tab_chosen(idx)
        else:
            idx = self.nav_click(self.list, x, y)
            if idx is None and self.tabs.item_at(x, y) is not None:
                self.focus = "tabs"
            self._act(idx)

    def motion(self, x: int, y: int) -> None:
        self.nav_motion(self.list if self.focus == "list" else self.tabs, x, y)

    def _tab_chosen(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        if idx == 2:
            self.app.goto(CampScreen(self.app))
        elif self._items:
            self.focus = "list"

    def _act(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        svc, hero = self.app.service, self.app.hero
        try:
            if self.mode == "buy":
                self.msg = svc.buy(hero, idx)
            else:
                self.msg = svc.sell(hero, idx)
            self.msg_err = False
            self.app.sfx("coin")
        except PixelQuestError as err:
            self.msg, self.msg_err = str(err), True
            self.app.sfx("error")
        self._rebuild()
        if not self._items:
            self.focus = "tabs"


# --------------------------------------------------------------------- TABERNA
class TavernScreen(Screen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.tabs = Menu(14, 34, 70, [Choice("CONTRATAR"), Choice("DESPEDIR"), Choice("SALIR")], row_h=12)
        self.list = Menu(110, 34, 200, [], rows=5, row_h=10)
        self.focus = "tabs"
        self.msg = ""
        self.msg_err = False
        self._members: list = []
        self._offers: list = []
        self._rebuild()

    @property
    def mode(self) -> str:
        return "dismiss" if self.tabs.cursor == 1 else "hire"

    def _rebuild(self) -> None:
        hero = self.app.hero
        if self.mode == "hire":
            self._offers = self.app.service.tavern_offers(hero)
            self._members = [o.preview for o in self._offers]
            self.list.set_choices([
                Choice(o.name.upper(), (not o.in_party) and hero.gold >= o.cost,
                       "EN GRUPO" if o.in_party else f"{o.cost} ORO") for o in self._offers])
        else:
            self._offers = []
            self._members = hero.companions
            self.list.set_choices([Choice(c.name.upper(), True, f"NV{c.level}") for c in self._members])

    def draw(self, fb: Framebuffer) -> None:
        hero, t = self.app.hero, self.app.t
        _stone_bg(fb)
        top_bar(fb, hero, f"TABERNA   GRUPO {len(hero.party)}/{hero.MAX_COMPANIONS + 1}")
        window(fb, 4, 26, 90, 54)
        self.tabs.draw(fb, t, active=self.focus == "tabs")
        member = self._members[self.list.cursor] if self._members else None
        window(fb, 4, 84, 90, 92)
        if member:
            fb.sprite(member_sprite(member.CLASS_KEY), 16, 92 - int(2 * abs(math.sin(t * 3))), 4)
            fb.text_center(49, 162, member.name.upper()[:12], C.WHITE, C.BLACK)
        window(fb, 98, 26, 218, 62)
        if not self._members:
            fb.text_center(207, 52, "(NADIE)", C.G2)
        self.list.draw(fb, t, active=self.focus == "list")
        window(fb, 98, 92, 218, 84)
        if member:
            fb.text(108, 98, f"{member.CLASS_NAME.upper()}  NV{member.level}", C.GOLD, C.BLACK)
            stats = [("HP", member.max_hp, C.LGREEN), ("MP", member.max_mp, C.CYAN),
                     ("ATK", member.attack_power, C.LRED), ("DEF", member.defense_power, C.SKY)]
            for i, (label, value, col) in enumerate(stats):
                x, y = 108 + (i % 2) * 100, 112 + (i // 2) * 11
                fb.text(x, y, label, C.G1)
                fb.text(x + 26, y, str(value), col)
            for i, line in enumerate(wrap("HABILIDAD: " + member.SPECIAL_NAME.upper(), 34)[:2]):
                fb.text(108, 140 + i * 10, line, C.WHITE)
            fb.text(108, 162, f"COSTE {member.SPECIAL_COST} MP", C.G1)
        window(fb, 4, 180, 312, 56)
        if self.msg:
            for i, line in enumerate(wrap(self.msg.upper(), 50)[:3]):
                fb.text(12, 188 + i * 10, line, C.LRED if self.msg_err else C.LGREEN, C.BLACK)
        else:
            if self.mode == "hire" and self._offers:
                for i, line in enumerate(wrap(self._offers[self.list.cursor].blurb.upper(), 50)[:2]):
                    fb.text(12, 188 + i * 10, line, C.WHITE)
            elif self.mode == "dismiss" and not self._members:
                fb.text(12, 188, "NO TIENES COMPAÑEROS QUE DESPEDIR.", C.G1)
            fb.text(12, 224, "LOS COMPAÑEROS SUBEN DE NIVEL CONTIGO", C.G2)

    def key(self, key: str, char: str = "") -> None:
        if key != "char":
            self.msg = ""
        if self.focus == "tabs":
            if key == "cancel":
                self.app.sfx("cancel")
                self.app.goto(CampScreen(self.app))
                return
            before = self.tabs.cursor
            idx = self.nav(self.tabs, key, char)
            if self.tabs.cursor != before:
                self.list.cursor = self.list.top = 0
                self._rebuild()
            self._tab_chosen(idx)
        elif key == "cancel":
            self.focus = "tabs"
            self.app.sfx("cancel")
        else:
            self._act(self.nav(self.list, key, char))

    def click(self, x: int, y: int, button: int = 1) -> None:
        if button == 3:
            self.key("cancel")
            return
        self.msg = ""
        if self.focus == "tabs":
            before = self.tabs.cursor
            idx = self.nav_click(self.tabs, x, y)
            if self.tabs.cursor != before:
                self.list.cursor = self.list.top = 0
                self._rebuild()
            self._tab_chosen(idx)
        else:
            idx = self.nav_click(self.list, x, y)
            if idx is None and self.tabs.item_at(x, y) is not None:
                self.focus = "tabs"
            self._act(idx)

    def motion(self, x: int, y: int) -> None:
        self.nav_motion(self.list if self.focus == "list" else self.tabs, x, y)

    def _tab_chosen(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        if idx == 2:
            self.app.goto(CampScreen(self.app))
        elif self._members:
            self.focus = "list"

    def _act(self, idx: Optional[int]) -> None:
        if idx is None:
            return
        svc, hero = self.app.service, self.app.hero
        try:
            self.msg = svc.recruit(hero, idx) if self.mode == "hire" else svc.dismiss(hero, idx)
            self.msg_err = False
            self.app.sfx("levelup" if self.mode == "hire" else "cancel")
        except PixelQuestError as err:
            self.msg, self.msg_err = str(err), True
            self.app.sfx("error")
        self._rebuild()
        if not self._members:
            self.focus = "tabs"


# ---------------------------------------------------------------------- ESTADO
class StatusScreen(Screen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.index = 0

    def draw(self, fb: Framebuffer) -> None:
        hero, t = self.app.hero, self.app.t
        party = hero.party
        self.index %= len(party)
        m = party[self.index]
        _stone_bg(fb)
        top_bar(fb, hero, f"ESTADO   < {self.index + 1}/{len(party)} >")
        window(fb, 4, 26, 110, 150)
        fb.sprite(member_sprite(m.CLASS_KEY), 20, 36 - int(2 * abs(math.sin(t * 3))), 5,
                  tint=None if m.is_alive else C.G3)
        fb.text_center(59, 124, m.name.upper()[:14], C.WHITE, C.BLACK)
        fb.text_center(59, 136, m.CLASS_NAME.upper(), C.GOLD)
        fb.text_center(59, 148, f"NIVEL {m.level}", C.G1)
        window(fb, 118, 26, 198, 150)
        rows = [("HP", m.hp, m.max_hp, hp_color(m.hp, m.max_hp)), ("MP", m.mp, m.max_mp, C.CYAN),
                ("XP", m.xp, m.xp_to_next, C.YELLOW)]
        for i, (label, cur, mx, col) in enumerate(rows):
            y = 36 + i * 14
            fb.text(128, y, label, C.SKY)
            bar(fb, 148, y + 1, 90, cur, mx, col, 4)
            fb.text_right(306, y, f"{cur}/{mx}", C.WHITE)
        fb.text(128, 82, "ATAQUE", C.G1); fb.text(190, 82, str(m.attack_power), C.LRED)
        fb.text(226, 82, "DEFENSA", C.G1); fb.text_right(306, 82, str(m.defense_power), C.SKY)
        for i, line in enumerate(wrap(f"HABILIDAD: {m.SPECIAL_NAME.upper()} ({m.SPECIAL_COST} MP)", 31)[:3]):
            fb.text(128, 98 + i * 10, line, C.WHITE)
        if m is hero:
            for i, (label, eq) in enumerate((("ARMA", hero.weapon), ("ARMADURA", hero.armor),
                                             ("ACCESORIO", hero.accessory))):
                fb.text(128, 132 + i * 13, label, C.G1)
                fb.text(190, 132 + i * 13, eq.name.upper()[:19] if eq else "-", C.WHITE if eq else C.G3)
        else:
            fb.text(128, 138, "COMPAÑERO DE VIAJE", C.G1)
        window(fb, 4, 180, 312, 56)
        fb.text(12, 190, f"PISO {hero.floor}  SALA {hero.rooms_in_floor}/{ROOMS_PER_FLOOR}", C.WHITE)
        fb.text(12, 202, f"ORO {hero.gold}", C.GOLD)
        fb.text(12, 224, "IZQ/DER: CAMBIAR DE MIEMBRO   ESC: VOLVER", C.G2)

    def key(self, key: str, char: str = "") -> None:
        n = len(self.app.hero.party)
        if key == "left":
            self.index = (self.index - 1) % n
            self.app.sfx("move")
        elif key == "right":
            self.index = (self.index + 1) % n
            self.app.sfx("move")
        elif key in ("cancel", "confirm"):
            self.app.sfx("cancel")
            self.app.goto(CampScreen(self.app))

    def click(self, x: int, y: int, button: int = 1) -> None:
        if button == 3:
            self.key("cancel")
        else:
            self.key("right")
