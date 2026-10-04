import random
import tempfile
import unittest
from pathlib import Path

from src.domain.exceptions import (
    CombatError, DuplicateHeroError, HeroNotFoundError, InventoryFullError, NotEnoughGoldError,
    PartyError, PartyFullError, SaveDataError,
)
from src.domain.models import Ether, Potion
from src.services.app_service import GameService, shop_catalog
from src.services.data_manager import DataManager


class TestServices(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "heroes.json"
        self.service = GameService(DataManager(str(self.path)), random.Random(7))

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_save_load(self):
        self.service.create_hero("Aria", "warrior")
        hero = self.service.load_hero("aria")
        self.assertEqual(hero.name, "Aria")
        self.assertEqual(len(hero.inventory), 1)

    def test_duplicate_and_missing(self):
        self.service.create_hero("Aria", "mage")
        with self.assertRaises(DuplicateHeroError):
            self.service.create_hero("ARIA", "rogue")
        with self.assertRaises(HeroNotFoundError):
            self.service.load_hero("Nadie")

    def test_corrupt_file(self):
        self.path.write_text("{no es json", encoding="utf-8")
        with self.assertRaises(SaveDataError):
            self.service.list_heroes()

    def test_buy_needs_gold(self):
        hero = self.service.create_hero("Aria", "warrior")
        names = [i.name for i in shop_catalog(hero.floor)]
        with self.assertRaises(NotEnoughGoldError):
            self.service.buy(hero, names.index("Armadura de Placas"))  # 110 de oro
        self.service.buy(hero, names.index("Poción Menor"))  # 15 de oro
        self.assertEqual(hero.gold, 5)

    def test_full_run_reaches_boss_and_next_floor(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.gain_xp(2000)  # héroe fuerte para el test
        hero.inventory.add(__import__("src.domain.models", fromlist=["Weapon"]).Weapon("Test", 30))
        hero.equip(len(hero.inventory) - 1)
        boss_beaten = False
        for _ in range(60):
            event = self.service.explore(hero)
            if event.enemy is None:
                continue
            session = self.service.start_combat(hero, event.enemy)
            while not session.is_over:
                session.player_attack()
            self.service.finish_combat(session)
            hero.heal(9999)
            if event.kind == "boss":
                boss_beaten = True
                break
        self.assertTrue(boss_beaten)
        self.assertEqual(hero.floor, 2)

    def test_cannot_flee_boss(self):
        hero = self.service.create_hero("Aria", "warrior")
        for _ in range(4):
            hero._rooms_in_floor = 4
        event = self.service.explore(hero)
        session = self.service.start_combat(hero, event.enemy)
        with self.assertRaises(CombatError):
            session.player_flee()


class TestContentAndParty(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = GameService(DataManager(str(Path(self.tmp.name) / "h.json")), random.Random(3))

    def tearDown(self):
        self.tmp.cleanup()

    def test_shop_grows_with_floor(self):
        self.assertGreater(len(shop_catalog(3)), len(shop_catalog(1)))
        self.assertGreater(len(shop_catalog(99)), len(shop_catalog(3)))
        self.assertGreaterEqual(len(shop_catalog(99)), 20)

    def test_sell_gives_half_value(self):
        hero = self.service.create_hero("Aria", "warrior")
        msg = self.service.sell(hero, 0)  # Poción Menor vale 15
        self.assertEqual(hero.gold, 20 + 7)
        self.assertIn("Vendiste", msg)
        self.assertEqual(len(hero.inventory), 0)

    def test_recruit_charges_gold_and_persists(self):
        hero = self.service.create_hero("Aria", "warrior")
        with self.assertRaises(NotEnoughGoldError):
            self.service.recruit(hero, 0)
        self.assertEqual(hero.companions, [])  # no queda a medias
        hero.earn_gold(500)
        self.service.recruit(hero, 0)
        self.assertEqual(len(self.service.load_hero("Aria").companions), 1)
        with self.assertRaises(PartyError):
            self.service.recruit(hero, 0)  # ya está en el grupo
        self.service.recruit(hero, 1)
        with self.assertRaises(PartyFullError):
            self.service.recruit(hero, 2)
        self.service.dismiss(hero, 0)
        self.assertEqual(len(hero.companions), 1)

    def test_recruited_companion_matches_hero_level(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.gain_xp(200)
        hero.earn_gold(999)
        self.service.recruit(hero, 0)
        self.assertEqual(hero.companions[0].level, hero.level)

    def test_group_combat_turn_order(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.earn_gold(999)
        self.service.recruit(hero, 0)
        self.service.recruit(hero, 1)
        enemy = self.service._spawn_enemy(1, 3)
        session = self.service.start_combat(hero, enemy)
        actors = []
        for _ in range(3):
            actors.append(session.current_actor.name)
            session.player_attack()
        self.assertEqual(actors, [m.name for m in hero.party])
        self.assertEqual(session.turn, 2)            # tras el 3.º, atacó el enemigo y empezó otra ronda
        self.assertIs(session.current_actor, hero)
        self.assertTrue(any(e.kind == "hit" for e in session.events))

    def test_enemy_hp_scales_with_party(self):
        solo = self.service._spawn_boss(1, 1)
        trio = self.service._spawn_boss(1, 3)
        self.assertGreater(trio.max_hp, solo.max_hp * 2)

    def test_cleric_heals_in_combat_and_needs_a_wounded_ally(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.earn_gold(999)
        self.service.recruit(hero, 0)  # Aria la clériga
        session = self.service.start_combat(hero, self.service._spawn_enemy(1, 2))
        session.player_defend()        # el héroe se defiende
        with self.assertRaises(CombatError):
            session.player_special()   # nadie herido todavía (la clériga no puede curar)
        hero.take_damage(50)
        session.player_special()
        self.assertTrue(any(e.kind == "heal" and e.target is hero for e in session.events))

    def test_item_in_combat_targets_ally(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.earn_gold(999)
        self.service.recruit(hero, 2)
        ally = hero.companions[0]
        ally.take_damage(30)
        session = self.service.start_combat(hero, self.service._spawn_enemy(1, 2))
        before = ally.hp
        session.player_use_item(0, 1)  # Poción Menor sobre el compañero
        self.assertGreater(ally.hp, before - 50)

    def test_fallen_members_get_up_after_battle(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.earn_gold(999)
        self.service.recruit(hero, 2)
        buddy = hero.companions[0]
        enemy = self.service._spawn_enemy(1, 2)
        session = self.service.start_combat(hero, enemy)
        buddy.take_damage(9999)
        enemy.take_damage(9999)
        session.events = []
        self.assertTrue(session.victory)
        self.service.finish_combat(session)
        self.assertTrue(buddy.is_alive)

    def test_defeat_when_whole_party_falls(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.earn_gold(999)
        self.service.recruit(hero, 0)
        session = self.service.start_combat(hero, self.service._spawn_enemy(1, 2))
        for m in hero.party:
            m.take_damage(9999)
        self.assertTrue(session.is_over)
        self.assertFalse(session.victory)
        lines = self.service.finish_combat(session)
        self.assertTrue(all(m.is_alive for m in hero.party))
        self.assertTrue(any("derrotado" in l for l in lines))

    def test_inn_restores_party(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.earn_gold(500)
        self.service.recruit(hero, 0)
        for m in hero.party:
            m.take_damage(40)
        self.service.rest(hero)
        self.assertTrue(all(m.hp == m.max_hp for m in hero.party))

    def test_use_item_outside_combat_on_companion(self):
        hero = self.service.create_hero("Aria", "warrior")
        hero.earn_gold(500)
        self.service.recruit(hero, 0)
        hero.companions[0].take_damage(60)
        hp = hero.companions[0].hp
        self.service.use_item(hero, 0, 1)
        self.assertGreater(hero.companions[0].hp, hp)

    def test_exploring_never_crashes_and_trap_never_kills(self):
        hero = self.service.create_hero("Aria", "warrior")
        for _ in range(300):
            hero._rooms_in_floor = 0
            event = self.service.explore(hero)
            self.assertTrue(all(m.is_alive for m in hero.party) or event.kind != "trap")

    def test_summaries(self):
        self.service.create_hero("Aria", "mage")
        s = self.service.list_summaries()
        self.assertEqual(s[0]["class_name"], "Mago")


if __name__ == "__main__":
    unittest.main()
