"""Pruebas de la interfaz gráfica SIN abrir ninguna ventana (no necesita Tkinter)."""
import random
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from src.services.app_service import GameService, shop_catalog
from src.services.content import BOSS_TEMPLATES, ENEMY_TEMPLATES, RECRUITS
from src.services.data_manager import DataManager
from src.ui.gui import font, sprites
from src.ui.gui.app import GameApp
from src.ui.gui.framebuffer import H, W, Framebuffer
from src.ui.gui.palette import C, NAMES
from src.ui.gui.sound import SFX, make_wav
from src.ui.gui.widgets import Choice, Dialogue, Menu, wrap
from src.domain.models import COMPANION_CLASSES, HERO_CLASSES


class TestRendering(unittest.TestCase):
    def test_png_is_valid(self):
        fb = Framebuffer()
        fb.clear(C.BLUE2)
        fb.text(4, 4, "¡HOLA MUNDO!", C.WHITE)
        data = fb.png(2)
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        w, h = struct.unpack(">II", data[16:24])
        self.assertEqual((w, h), (W * 2, H * 2))
        idat = data[data.index(b"IDAT") + 4: data.index(b"IEND") - 8]
        self.assertEqual(len(zlib.decompress(idat)), h * (w * 3 + 1))

    def test_drawing_is_clipped(self):
        fb = Framebuffer()
        fb.rect(-10, -10, 400, 400, C.RED)
        fb.text(310, 235, "ABC", C.WHITE)
        fb.sprite(sprites.member_sprite("mage"), -8, 230, 3)
        self.assertEqual(len(fb.px), W * H)

    def test_font_has_all_game_text(self):
        texts = []
        texts += [i.name + i.describe() + i.description for i in shop_catalog()]
        texts += [t[0] for t in ENEMY_TEMPLATES] + [t[0] for t in BOSS_TEMPLATES]
        texts += [r.name + r.blurb for r in RECRUITS]
        texts += [c.CLASS_NAME + c.SPECIAL_NAME for c in list(HERO_CLASSES.values()) + list(COMPANION_CLASSES.values())]
        texts += ["¡VICTORIA! ¿SOBRE QUIÉN? ÑANDÚ PÍCARO CLÉRIGO ALQUIMISTA 0123456789"]
        for text in texts:
            self.assertTrue(font.supports(text), text)

    def test_palette_names_unique(self):
        self.assertEqual(len(NAMES), len(set(NAMES)))

    def test_all_sprites_exist(self):
        for key in list(HERO_CLASSES) + list(COMPANION_CLASSES):
            self.assertEqual((sprites.member_sprite(key).w, sprites.member_sprite(key).h), (16, 16))
        for name in [t[0] for t in ENEMY_TEMPLATES] + [t[0] for t in BOSS_TEMPLATES]:
            spr, scale = sprites.enemy_sprite(name)
            self.assertEqual((spr.w, spr.h), (16, 16))
        self.assertEqual(sprites.enemy_sprite("Rey Slime Nv7", True)[1], 6)

    def test_wrap_and_menu(self):
        self.assertEqual(wrap("uno dos tres", 7), ["uno dos", "tres"])
        menu = Menu(0, 0, 50, [Choice("A"), Choice("B", False), Choice("C")], digits=True)
        self.assertEqual(menu.key("confirm"), 0)
        menu.key("down")
        self.assertEqual(menu.key("confirm"), Menu.DENIED)
        self.assertEqual(menu.key("char", "3"), 2)

    def test_dialogue_typewriter_and_paging(self):
        d = Dialogue(0, 0, 100, 30)
        d.say("palabra " * 20)
        self.assertFalse(d.typed)
        self.assertFalse(d.advance())   # primero completa el texto
        pages = 1
        while d.active:
            d.advance()
            pages += 1
        self.assertGreater(pages, 1)

    def test_sound_wav(self):
        for name, notes in SFX.items():
            self.assertEqual(make_wav(notes)[:4], b"RIFF", name)


class TestGameApp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = GameService(DataManager(str(Path(self.tmp.name) / "h.json")), random.Random(4))
        self.app = GameApp(self.service)

    def tearDown(self):
        self.tmp.cleanup()

    def name(self):
        return type(self.app.screen).__name__

    def tick(self, seconds=1.0):
        for _ in range(int(seconds / 0.04)):
            self.app.update(0.04)
            self.app.render()

    def test_create_hero_flow(self):
        self.assertEqual(self.name(), "TitleScreen")
        self.app.key("confirm")
        self.assertEqual(self.name(), "NewHeroScreen")
        self.assertTrue(self.app.wants_text)
        self.app.key("confirm")                      # nombre vacío: se queda
        self.assertEqual(self.name(), "NewHeroScreen")
        for ch in "Lira":
            self.app.key("char", ch)
        self.app.key("confirm")
        self.app.key("down")                         # Mago
        self.app.key("confirm")
        self.assertEqual(self.name(), "CampScreen")
        self.assertEqual(self.app.hero.CLASS_NAME, "Mago")
        self.assertIn("Lira", self.service.list_heroes())

    def test_duplicate_name_shows_error(self):
        self.service.create_hero("Lira", "mage")
        self.app.key("confirm")
        for ch in "lira":
            self.app.key("char", ch)
        self.app.key("confirm")
        self.app.key("confirm")
        self.assertEqual(self.name(), "NewHeroScreen")
        self.assertIn("EXISTE", self.app.screen.error)

    def test_hub_navigation_and_buying(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.earn_gold(200)
        self.app.hero = hero
        from src.ui.gui.screens_camp import CampScreen
        self.app.goto(CampScreen(self.app))
        self.app.key("down"); self.app.key("down")   # TIENDA
        self.app.key("confirm")
        self.assertEqual(self.name(), "ShopScreen")
        self.app.key("confirm")                      # entrar a la lista
        self.app.key("confirm")                      # comprar Poción Menor
        self.assertEqual(len(hero.inventory), 2)
        self.app.key("cancel"); self.app.key("cancel")
        self.assertEqual(self.name(), "CampScreen")

    def test_tavern_hires_companion(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.earn_gold(300)
        self.app.hero = hero
        from src.ui.gui.screens_camp import TavernScreen
        self.app.goto(TavernScreen(self.app))
        self.app.key("confirm")                      # lista de contratación
        self.app.key("confirm")                      # contratar a Aria la clériga
        self.assertEqual(len(hero.companions), 1)
        self.assertIn("SE UNE", self.app.screen.msg.upper())

    def test_full_fight_with_party_reaches_camp(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.earn_gold(500)
        self.service.recruit(hero, 0)
        self.app.hero = hero
        from src.ui.gui.screens_combat import CombatScreen
        enemy = self.service._spawn_enemy(1, 2)
        self.app.goto(CombatScreen(self.app, enemy))
        self.tick(2.0)
        self.assertEqual(self.app.screen.mode, "command")
        for _ in range(400):
            if self.name() != "CombatScreen":
                break
            self.app.key("confirm")                  # ATACAR / avanzar textos
            self.tick(0.3)
        self.assertEqual(self.name(), "CampScreen")
        self.assertTrue(all(m.is_alive for m in hero.party))

    def test_item_menu_in_combat(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.take_damage(50)
        self.app.hero = hero
        from src.ui.gui.screens_combat import CombatScreen
        self.app.goto(CombatScreen(self.app, self.service._spawn_enemy(1, 1)))
        self.tick(2.0)
        for _ in range(3):
            self.app.key("down")                     # OBJETO
        self.app.key("confirm")
        self.assertEqual(self.app.screen.mode, "item")
        self.app.key("confirm")
        self.assertEqual(self.app.screen.mode, "target")
        self.app.key("confirm")                      # usar sobre el héroe
        self.assertEqual(self.app.screen.mode, "playback")
        self.assertEqual(len(hero.inventory), 0)

    def test_random_input_never_crashes(self):
        rng = random.Random(9)
        self.service.create_hero("Zed", "rogue")
        for step in range(2500):
            r = rng.random()
            if r < 0.6:
                self.app.key(rng.choice(["up", "down", "left", "right", "confirm", "confirm", "cancel", "backspace"]))
            elif r < 0.65:
                self.app.key("char", rng.choice("abc ñ1"))
            elif r < 0.75:
                self.app.click(rng.randrange(W), rng.randrange(H), rng.choice([1, 3]))
            for _ in range(rng.randrange(1, 10)):
                self.app.update(0.05)
            if step % 5 == 0:
                self.app.render()
            self.app.should_quit = False
            if self.app.hero and step % 40 == 0:
                self.app.hero.earn_gold(300)


if __name__ == "__main__":
    unittest.main()
