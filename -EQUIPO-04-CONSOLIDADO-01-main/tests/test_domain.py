import random
import unittest

from src.domain.exceptions import (
    CombatError, InvalidItemError, InvalidNameError, InventoryFullError, ItemNotFoundError,
    PartyError, PartyFullError,
)
from src.domain.models import (
    COMPANION_CLASSES, Accessory, Alchemist, Archer, Armor, Boss, Cleric, Enemy, Ether, Inventory,
    Knight, Mage, Potion, Rogue, Warrior, Weapon, hero_from_dict,
)


class TestDomain(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(1)

    def test_invalid_name(self):
        with self.assertRaises(InvalidNameError):
            Warrior("   ")

    def test_level_up(self):
        hero = Warrior("Aria")
        self.assertEqual(hero.gain_xp(50), 1)
        self.assertEqual(hero.level, 2)
        self.assertGreater(hero.max_hp, 120)

    def test_inventory_full(self):
        inv = Inventory(capacity=1)
        inv.add(Potion("P", 10))
        with self.assertRaises(InventoryFullError):
            inv.add(Potion("P2", 10))
        with self.assertRaises(ItemNotFoundError):
            inv.get(5)

    def test_equip_swaps_items(self):
        hero = Warrior("Aria")
        hero.inventory.add(Weapon("A", 3))
        hero.inventory.add(Weapon("B", 5))
        hero.equip(0)
        hero.equip(0)  # ahora B en posición 0
        self.assertEqual(hero.weapon.name, "B")
        self.assertEqual(hero.inventory.items[0].name, "A")
        self.assertEqual(hero.attack_power, 12 + 5)

    def test_cannot_equip_potion(self):
        hero = Mage("Merlin")
        hero.inventory.add(Potion("P", 10))
        with self.assertRaises(InvalidItemError):
            hero.equip(0)

    def test_min_damage_is_one(self):
        hero = Warrior("Aria")
        tank = Enemy("Tanque", 50, 1, 999, 1, 1)
        self.assertGreaterEqual(hero.compute_damage(tank, self.rng), 1)

    def test_special_needs_mp(self):
        hero = Rogue("Sombra")
        enemy = Enemy("Dummy", 500, 1, 0, 1, 1)
        for _ in range(3):
            hero.special_attack(enemy, self.rng)
        with self.assertRaises(CombatError):
            hero.special_attack(enemy, self.rng)

    def test_guard_halves_damage(self):
        hero = Warrior("Aria")
        hero.guard()
        self.assertEqual(hero.take_damage(10), 5)

    def test_boss_enrages(self):
        boss = Boss("Jefe", 100, 10, 0, 1, 1)
        self.assertEqual(boss.attack_power, 10)
        boss.take_damage(60)
        self.assertTrue(boss.enraged)
        self.assertEqual(boss.attack_power, 15)

    def test_serialization_roundtrip(self):
        hero = Mage("Merlin")
        hero.inventory.add(Weapon("Bastón", 4, 10))
        hero.inventory.add(Armor("Túnica", 2, 10))
        hero.equip(0)
        hero.gain_xp(60)
        clone = hero_from_dict(hero.to_dict())
        self.assertEqual(clone.to_dict(), hero.to_dict())
        self.assertIsInstance(clone, Mage)


class TestParty(unittest.TestCase):
    def setUp(self):
        self.rng = random.Random(2)

    def test_recruit_limit_and_duplicates(self):
        hero = Warrior("Aria")
        hero.recruit(Cleric("Lia"))
        with self.assertRaises(PartyError):
            hero.recruit(Archer("lia"))
        hero.recruit(Knight("Gar"))
        with self.assertRaises(PartyFullError):
            hero.recruit(Alchemist("Zed"))
        self.assertEqual([m.name for m in hero.party], ["Aria", "Lia", "Gar"])

    def test_dismiss(self):
        hero = Warrior("Aria")
        hero.recruit(Cleric("Lia"))
        self.assertEqual(hero.dismiss(0).name, "Lia")
        with self.assertRaises(PartyError):
            hero.dismiss(0)

    def test_cleric_heals_ally(self):
        cleric, ally = Cleric("Lia"), Warrior("Aria")
        ally.take_damage(60)
        healed = cleric.special_attack(ally, self.rng)
        self.assertGreater(healed, 0)
        self.assertEqual(ally.hp, 120 - 60 + healed)

    def test_companion_specials_cost_mp(self):
        enemy = Enemy("Dummy", 900, 1, 0, 1, 1)
        for cls in (Archer, Knight, Alchemist):
            member = cls("X")
            before = member.mp
            dmg = member.special_attack(enemy, self.rng)
            self.assertGreater(dmg, 0)
            self.assertEqual(member.mp, before - cls.SPECIAL_COST)

    def test_knight_shield_strike_guards(self):
        knight = Knight("Gar")
        knight.special_attack(Enemy("Dummy", 900, 1, 0, 1, 1), self.rng)
        self.assertEqual(knight.take_damage(10), 5)

    def test_set_level_and_revive(self):
        member = Archer("Robin")
        member.set_level(4)
        self.assertEqual(member.level, 4)
        self.assertGreater(member.max_hp, 90)
        member.take_damage(9999)
        member.revive(0.25)
        self.assertEqual(member.hp, int(member.max_hp * 0.25))

    def test_party_serialization_roundtrip(self):
        hero = Mage("Merlin")
        hero.recruit(Cleric("Lia"))
        hero.companions[0].take_damage(20)
        clone = hero_from_dict(hero.to_dict())
        self.assertEqual(clone.to_dict(), hero.to_dict())
        self.assertEqual(clone.companions[0].hp, hero.companions[0].hp)
        self.assertIn("cleric", COMPANION_CLASSES)

    def test_old_save_without_party_still_loads(self):
        data = Warrior("Aria").to_dict()
        del data["companions"], data["accessory"]
        self.assertEqual(hero_from_dict(data).companions, [])


class TestNewItems(unittest.TestCase):
    def test_accessory_adds_both_bonuses(self):
        hero = Warrior("Aria")
        hero.inventory.add(Accessory("Brazalete", 2, 3, 10))
        hero.equip(0)
        self.assertEqual(hero.attack_power, 14)
        self.assertEqual(hero.defense_power, 9)
        self.assertEqual(hero_from_dict(hero.to_dict()).accessory.name, "Brazalete")

    def test_ether_restores_mp_on_ally_and_potion_needs_living_target(self):
        hero, ally = Warrior("Aria"), Cleric("Lia")
        hero.recruit(ally)
        ally.special_attack(hero, random.Random(1))
        hero.inventory.add(Ether("Éter", 20, 5))
        hero.use_item(0, ally)
        self.assertEqual(ally.mp, ally.max_mp)
        ally.take_damage(9999)
        hero.inventory.add(Potion("P", 40, 5))
        with self.assertRaises(InvalidItemError):
            hero.use_item(0, ally)


if __name__ == "__main__":
    unittest.main()