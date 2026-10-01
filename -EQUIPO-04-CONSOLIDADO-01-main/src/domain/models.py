"""Capa 1 - Dominio (POO pura).

Contiene: objetos (Item, Weapon, Armor, Accessory, Potion, Ether), Inventory,
personajes (Character -> PartyMember -> Hero[Warrior, Mage, Rogue] / Companion
[Cleric, Archer, Knight, Alchemist] ; Character -> Enemy -> Boss).
No sabe nada de consola ni de archivos: solo reglas del juego.
"""
from __future__ import annotations

import random

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from .exceptions import (
    CombatError,
    InvalidItemError,
    InvalidNameError,
    InvalidStatError,
    InventoryFullError,
    ItemNotFoundError,
    NotEnoughGoldError,
    PartyError,
    PartyFullError,
    SaveDataError,
)

MAX_NAME_LENGTH = 20


def validate_name(name: str) -> str:
    """Valida y normaliza un nombre."""
    if not isinstance(name, str) or not name.strip():
        raise InvalidNameError("El nombre no puede estar vacío.")
    name = name.strip()
    if len(name) > MAX_NAME_LENGTH:
        raise InvalidNameError(f"El nombre no puede superar {MAX_NAME_LENGTH} caracteres.")
    return name


# ---------------------------------------------------------------- OBJETOS
class Item(ABC):
    """Clase base abstracta de todos los objetos."""

    KIND = "item"

    def __init__(self, name: str, value: int = 0, description: str = "") -> None:
        self._name = validate_name(name)
        if value < 0:
            raise InvalidStatError("El valor de un objeto no puede ser negativo.")
        self._value = int(value)
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> int:
        return self._value

    @property
    def description(self) -> str:
        return self._description

    @abstractmethod
    def describe(self) -> str:
        """Texto corto con el efecto del objeto."""

    def _extra(self) -> Dict[str, Any]:
        return {}

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "kind": self.KIND,
            "name": self._name,
            "value": self._value,
            "description": self._description,
        }
        data.update(self._extra())
        return data


class Weapon(Item):
    KIND = "weapon"

    def __init__(self, name: str, attack_bonus: int, value: int = 0, description: str = "") -> None:
        super().__init__(name, value, description)
        if attack_bonus < 0:
            raise InvalidStatError("El bonus de ataque no puede ser negativo.")
        self._attack_bonus = int(attack_bonus)

    @property
    def attack_bonus(self) -> int:
        return self._attack_bonus

    def describe(self) -> str:
        return f"Arma  +{self._attack_bonus} ATK"

    def _extra(self) -> Dict[str, Any]:
        return {"attack_bonus": self._attack_bonus}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Weapon":
        return cls(data["name"], data["attack_bonus"], data.get("value", 0), data.get("description", ""))


class Armor(Item):
    KIND = "armor"

    def __init__(self, name: str, defense_bonus: int, value: int = 0, description: str = "") -> None:
        super().__init__(name, value, description)
        if defense_bonus < 0:
            raise InvalidStatError("El bonus de defensa no puede ser negativo.")
        self._defense_bonus = int(defense_bonus)

    @property
    def defense_bonus(self) -> int:
        return self._defense_bonus

    def describe(self) -> str:
        return f"Armadura  +{self._defense_bonus} DEF"

    def _extra(self) -> Dict[str, Any]:
        return {"defense_bonus": self._defense_bonus}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Armor":
        return cls(data["name"], data["defense_bonus"], data.get("value", 0), data.get("description", ""))


class Potion(Item):
    KIND = "potion"

    def __init__(self, name: str, heal_amount: int, value: int = 0, description: str = "") -> None:
        super().__init__(name, value, description)
        if heal_amount <= 0:
            raise InvalidStatError("Una poción debe curar más de 0 HP.")
        self._heal_amount = int(heal_amount)

    @property
    def heal_amount(self) -> int:
        return self._heal_amount

    def describe(self) -> str:
        return f"Poción  cura {self._heal_amount} HP"

    def _extra(self) -> Dict[str, Any]:
        return {"heal_amount": self._heal_amount}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Potion":
        return cls(data["name"], data["heal_amount"], data.get("value", 0), data.get("description", ""))


class Accessory(Item):
    """Tercer espacio de equipo: da un pequeño bonus de ATK y/o DEF."""

    KIND = "accessory"

    def __init__(self, name: str, attack_bonus: int = 0, defense_bonus: int = 0,
                 value: int = 0, description: str = "") -> None:
        super().__init__(name, value, description)
        if attack_bonus < 0 or defense_bonus < 0:
            raise InvalidStatError("Los bonus de un accesorio no pueden ser negativos.")
        self._attack_bonus = int(attack_bonus)
        self._defense_bonus = int(defense_bonus)

    @property
    def attack_bonus(self) -> int:
        return self._attack_bonus

    @property
    def defense_bonus(self) -> int:
        return self._defense_bonus

    def describe(self) -> str:
        parts = []
        if self._attack_bonus:
            parts.append(f"+{self._attack_bonus} ATK")
        if self._defense_bonus:
            parts.append(f"+{self._defense_bonus} DEF")
        return "Accesorio  " + " ".join(parts)

    def _extra(self) -> Dict[str, Any]:
        return {"attack_bonus": self._attack_bonus, "defense_bonus": self._defense_bonus}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Accessory":
        return cls(data["name"], data.get("attack_bonus", 0), data.get("defense_bonus", 0),
                   data.get("value", 0), data.get("description", ""))


class Ether(Item):
    """Restaura MP."""

    KIND = "ether"

    def __init__(self, name: str, mp_amount: int, value: int = 0, description: str = "") -> None:
        super().__init__(name, value, description)
        if mp_amount <= 0:
            raise InvalidStatError("Un éter debe restaurar más de 0 MP.")
        self._mp_amount = int(mp_amount)

    @property
    def mp_amount(self) -> int:
        return self._mp_amount

    def describe(self) -> str:
        return f"Éter  restaura {self._mp_amount} MP"

    def _extra(self) -> Dict[str, Any]:
        return {"mp_amount": self._mp_amount}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ether":
        return cls(data["name"], data["mp_amount"], data.get("value", 0), data.get("description", ""))


_ITEM_TYPES = {"weapon": Weapon, "armor": Armor, "potion": Potion,
               "accessory": Accessory, "ether": Ether}


def item_from_dict(data: Dict[str, Any]) -> Item:
    """Reconstruye un objeto desde un diccionario (para cargar partidas)."""
    try:
        return _ITEM_TYPES[data["kind"]].from_dict(data)
    except (KeyError, TypeError) as exc:
        raise SaveDataError(f"Objeto inválido en el guardado: {data!r}") from exc


class Inventory:
    """Mochila con capacidad limitada."""

    def __init__(self, capacity: int = 10) -> None:
        if capacity <= 0:
            raise InvalidStatError("La capacidad debe ser mayor a 0.")
        self._capacity = capacity
        self._items: List[Item] = []

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def items(self) -> List[Item]:
        return list(self._items)

    @property
    def is_full(self) -> bool:
        return len(self._items) >= self._capacity

    def __len__(self) -> int:
        return len(self._items)

    def add(self, item: Item) -> None:
        if self.is_full:
            raise InventoryFullError(f"Inventario lleno ({self._capacity} objetos).")
        self._items.append(item)

    def get(self, index: int) -> Item:
        if not 0 <= index < len(self._items):
            raise ItemNotFoundError("No hay ningún objeto en esa posición.")
        return self._items[index]

    def remove_at(self, index: int) -> Item:
        self.get(index)
        return self._items.pop(index)


# ------------------------------------------------------------- PERSONAJES
class Character(ABC):
    """Clase base abstracta: héroes y enemigos comparten combate básico."""

    def __init__(self, name: str, max_hp: int, attack: int, defense: int, level: int = 1) -> None:
        clean_name = name.strip()
        
        if not clean_name or len(clean_name) > 20:
            raise InvalidNameError("El nombre debe tener entre 1 y 20 caracteres.")
        if max_hp <= 0:
            raise InvalidStatError("Los HP máximos deben ser mayores a 0.")
        if attack < 0 or defense < 0:
            raise InvalidStatError("Ataque y defensa no pueden ser negativos.")
        
        # Asignar directamente a las variables protegidas con guion bajo
        self._name = clean_name
        self._level = int(level)
        self._max_hp = int(max_hp)
        self._hp = int(max_hp)
        self._attack = int(attack)
        self._defense = int(defense)
        self._guarding = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def level(self) -> int:
        return self._level

    @property
    def is_alive(self) -> bool:
        return self._hp > 0

    @property
    @abstractmethod
    def attack_power(self) -> int:
        """Ataque total (base + equipo / furia)."""
        pass

    @property
    @abstractmethod
    def defense_power(self) -> int:
        """Defensa total."""
        pass

    def compute_damage(self, target: "Character", rng: random.Random) -> int:
        raw = self.attack_power + rng.randint(-2, 2)
        return max(1, raw - target.defense_power)

    def attack_target(self, target: "Character", rng: random.Random) -> int:
        return target.take_damage(self.compute_damage(target, rng))

    def take_damage(self, amount: int) -> int:
        if amount < 0:
            raise InvalidStatError("El daño no puede ser negativo.")
        if self._guarding:
            amount = max(1, amount // 2)
            self._guarding = False
        actual = min(amount, self._hp)
        self._hp -= actual
        return actual

    def heal(self, amount: int) -> int:
        if amount < 0:
            raise InvalidStatError("La curación no puede ser negativa.")
        healed = min(amount, self._max_hp - self._hp)
        self._hp += healed
        return healed

    def guard(self) -> None:
        self._guarding = True

    def stop_guard(self) -> None:
        self._guarding = False

class PartyMember(Character, ABC):
    """Miembro del grupo (héroe o compañero): tiene MP, XP, subida de nivel y
    una habilidad especial propia (polimorfismo)."""

    CLASS_KEY = "member"
    CLASS_NAME = "Aventurero"
    SPECIAL_NAME = "Habilidad"
    SPECIAL_COST = 10
    SPECIAL_ON_ALLY = False  # True si la habilidad se lanza sobre un aliado (curar)
    GROWTH: Tuple[int, int, int] = (10, 2, 1)  # HP, ATK, DEF por nivel
    MP_GROWTH = 3

    def __init__(self, name: str, max_hp: int, attack: int, defense: int, max_mp: int) -> None:
        super().__init__(name, max_hp, attack, defense)
        if max_mp < 0:
            raise InvalidStatError("Los MP máximos no pueden ser negativos.")
        self._max_mp = int(max_mp)
        self._mp = int(max_mp)
        self._xp = 0

    # ---- propiedades
    @property
    def mp(self) -> int:
        return self._mp

    @property
    def max_mp(self) -> int:
        return self._max_mp

    @property
    def xp(self) -> int:
        return self._xp

    @property
    def xp_to_next(self) -> int:
        return 50 * self._level

    @property
    def special_short_name(self) -> str:
        """Nombre de la habilidad sin la aclaración entre paréntesis."""
        return self.SPECIAL_NAME.split(" (")[0]

    @property
    def attack_power(self) -> int:
        return self._attack

    @property
    def defense_power(self) -> int:
        return self._defense

    # ---- progreso
    def _level_up(self) -> None:
        self._level += 1
        hp_g, atk_g, def_g = self.GROWTH
        self._max_hp += hp_g
        self._attack += atk_g
        self._defense += def_g
        self._max_mp += self.MP_GROWTH
        self._hp = self._max_hp
        self._mp = self._max_mp

    def gain_xp(self, amount: int) -> int:
        """Suma XP y devuelve cuántos niveles subió."""
        if amount < 0:
            raise InvalidStatError("La XP no puede ser negativa.")
        self._xp += amount
        levels = 0
        while self._xp >= self.xp_to_next:
            self._xp -= self.xp_to_next
            self._level_up()
            levels += 1
        return levels

    def regen_mp(self, amount: int = 2) -> None:
        self._mp = min(self._max_mp, self._mp + amount)

    def restore_mp(self, amount: int) -> int:
        if amount < 0:
            raise InvalidStatError("La recuperación de MP no puede ser negativa.")
        restored = min(amount, self._max_mp - self._mp)
        self._mp += restored
        return restored

    def revive(self, fraction: float = 0.25) -> None:
        """Levanta a un miembro caído con una fracción de su HP máximo."""
        if not self.is_alive:
            self._hp = max(1, int(self._max_hp * fraction))
            self._guarding = False

    # ---- habilidad especial
    def special_attack(self, target: Character, rng: random.Random) -> int:
        """Gasta MP y ejecuta la habilidad. Devuelve daño causado (o HP curados)."""
        if self._mp < self.SPECIAL_COST:
            raise CombatError("MP insuficiente para la habilidad especial.")
        self._mp -= self.SPECIAL_COST
        return self._special(target, rng)

    @abstractmethod
    def _special(self, target: Character, rng: random.Random) -> int:
        """Ejecuta la habilidad y devuelve el daño causado / HP curados."""

    # ---- serialización
    def _base_dict(self) -> Dict[str, Any]:
        return {
            "class": self.CLASS_KEY,
            "name": self._name,
            "level": self._level,
            "max_hp": self._max_hp,
            "hp": self._hp,
            "attack": self._attack,
            "defense": self._defense,
            "max_mp": self._max_mp,
            "mp": self._mp,
            "xp": self._xp,
        }

    def _load_base(self, data: Dict[str, Any]) -> None:
        self._level = data["level"]
        self._max_hp = data["max_hp"]
        self._hp = data["hp"]
        self._attack = data["attack"]
        self._defense = data["defense"]
        self._max_mp = data["max_mp"]
        self._mp = data["mp"]
        self._xp = data["xp"]


# ------------------------------------------------------------ COMPAÑEROS
class Companion(PartyMember, ABC):
    """Aliado reclutable en la taberna (como los personajes de un JRPG).
    Sube de nivel con el héroe y actúa en su propio turno durante el combate."""

    def set_level(self, target_level: int) -> None:
        """Lo lleva al nivel indicado aplicando las mismas subidas de stats."""
        while self._level < target_level:
            self._level_up()

    def to_dict(self) -> Dict[str, Any]:
        return self._base_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Companion":
        member = cls(data["name"])  # type: ignore[call-arg]
        member._load_base(data)
        return member


class Cleric(Companion):
    CLASS_KEY = "cleric"
    CLASS_NAME = "Clérigo"
    SPECIAL_NAME = "Curar (cura a un aliado)"
    SPECIAL_COST = 8
    SPECIAL_ON_ALLY = True
    GROWTH = (9, 2, 1)
    MP_GROWTH = 4

    def __init__(self, name: str) -> None:
        super().__init__(name, max_hp=85, attack=9, defense=4, max_mp=45)

    def _special(self, target: Character, rng: random.Random) -> int:
        return target.heal(self.attack_power * 2 + 12 + rng.randint(0, 4))


class Archer(Companion):
    CLASS_KEY = "archer"
    CLASS_NAME = "Arquero"
    SPECIAL_NAME = "Flecha Certera (ignora defensa)"
    SPECIAL_COST = 8
    GROWTH = (10, 3, 1)

    def __init__(self, name: str) -> None:
        super().__init__(name, max_hp=90, attack=14, defense=3, max_mp=25)

    def _special(self, target: Character, rng: random.Random) -> int:
        return target.take_damage(self.attack_power + 5 + rng.randint(0, 3))


class Knight(Companion):
    CLASS_KEY = "knight"
    CLASS_NAME = "Caballero"
    SPECIAL_NAME = "Golpe de Escudo (+guardia)"
    SPECIAL_COST = 8
    GROWTH = (16, 2, 2)
    MP_GROWTH = 2

    def __init__(self, name: str) -> None:
        super().__init__(name, max_hp=140, attack=11, defense=8, max_mp=15)

    def _special(self, target: Character, rng: random.Random) -> int:
        dmg = target.take_damage(self.compute_damage(target, rng) + 3)
        self.guard()
        return dmg


class Alchemist(Companion):
    CLASS_KEY = "alchemist"
    CLASS_NAME = "Alquimista"
    SPECIAL_NAME = "Bomba Ácida (ignora defensa)"
    SPECIAL_COST = 12
    GROWTH = (8, 3, 1)
    MP_GROWTH = 3

    def __init__(self, name: str) -> None:
        super().__init__(name, max_hp=80, attack=12, defense=3, max_mp=40)

    def _special(self, target: Character, rng: random.Random) -> int:
        return target.take_damage(int(self.attack_power * 1.6) + 4 + rng.randint(0, 3))


COMPANION_CLASSES = {c.CLASS_KEY: c for c in (Cleric, Archer, Knight, Alchemist)}


def companion_from_dict(data: Dict[str, Any]) -> Companion:
    try:
        return COMPANION_CLASSES[data["class"]].from_dict(data)
    except (KeyError, TypeError, ValueError) as exc:
        raise SaveDataError("Datos de compañero inválidos en el guardado.") from exc


# ---------------------------------------------------------------- HÉROES
class Hero(PartyMember, ABC):
    """Héroe jugable (líder del grupo). Tiene inventario, equipo y oro."""

    CLASS_KEY = "hero"
    CLASS_NAME = "Héroe"
    MAX_COMPANIONS = 2

    def __init__(self, name: str, max_hp: int, attack: int, defense: int, max_mp: int) -> None:
        super().__init__(name, max_hp, attack, defense, max_mp)
        self._gold = 20
        self._inventory = Inventory()
        self._weapon: Optional[Weapon] = None
        self._armor: Optional[Armor] = None
        self._accessory: Optional[Accessory] = None
        self._floor = 1
        self._rooms_in_floor = 0
        self._companions: List[Companion] = []

    # ---- propiedades
    @property
    def gold(self) -> int:
        return self._gold

    @property
    def inventory(self) -> Inventory:
        return self._inventory

    @property
    def weapon(self) -> Optional[Weapon]:
        return self._weapon

    @property
    def armor(self) -> Optional[Armor]:
        return self._armor

    @property
    def accessory(self) -> Optional[Accessory]:
        return self._accessory

    @property
    def floor(self) -> int:
        return self._floor

    @property
    def rooms_in_floor(self) -> int:
        return self._rooms_in_floor

    @property
    def attack_power(self) -> int:
        return (self._attack
                + (self._weapon.attack_bonus if self._weapon else 0)
                + (self._accessory.attack_bonus if self._accessory else 0))

    @property
    def defense_power(self) -> int:
        return (self._defense
                + (self._armor.defense_bonus if self._armor else 0)
                + (self._accessory.defense_bonus if self._accessory else 0))

    # ---- grupo
    @property
    def companions(self) -> List[Companion]:
        return list(self._companions)

    @property
    def party(self) -> List[PartyMember]:
        """El héroe siempre va primero, seguido de sus compañeros."""
        return [self] + list(self._companions)

    @property
    def living_party(self) -> List[PartyMember]:
        return [m for m in self.party if m.is_alive]

    def recruit(self, companion: Companion) -> None:
        if len(self._companions) >= self.MAX_COMPANIONS:
            raise PartyFullError(f"Tu grupo ya está completo ({self.MAX_COMPANIONS} compañeros).")
        if any(c.name.lower() == companion.name.lower() for c in self._companions):
            raise PartyError(f"{companion.name} ya está en tu grupo.")
        self._companions.append(companion)

    def dismiss(self, index: int) -> Companion:
        if not 0 <= index < len(self._companions):
            raise PartyError("No hay ningún compañero en esa posición.")
        return self._companions.pop(index)

    # ---- progreso
    def earn_gold(self, amount: int) -> None:
        if amount < 0:
            raise InvalidStatError("No se puede ganar oro negativo.")
        self._gold += amount

    def spend_gold(self, amount: int) -> None:
        if amount > self._gold:
            raise NotEnoughGoldError(f"Necesitas {amount} de oro y solo tienes {self._gold}.")
        self._gold -= amount

    def advance_room(self) -> None:
        self._rooms_in_floor += 1

    def next_floor(self) -> None:
        self._floor += 1
        self._rooms_in_floor = 0

    def full_restore_partial(self, fraction: float = 0.3) -> int:
        healed = self.heal(int(self._max_hp * fraction))
        self._mp = self._max_mp
        return healed

    def revive_after_defeat(self) -> int:
        """Penalización por morir: pierde mitad del oro y reinicia el piso."""
        lost = self._gold // 2
        self._gold -= lost
        self._hp = max(1, self._max_hp // 2)
        self._mp = self._max_mp
        self._rooms_in_floor = 0
        self._guarding = False
        return lost

    # ---- inventario / equipo
    def equip(self, index: int) -> str:
        item = self._inventory.get(index)
        if isinstance(item, Weapon):
            self._inventory.remove_at(index)
            old, self._weapon = self._weapon, item
            if old:
                self._inventory.add(old)
            return f"{self.name} equipa {item.name} (+{item.attack_bonus} ATK)."
        if isinstance(item, Armor):
            self._inventory.remove_at(index)
            old, self._armor = self._armor, item
            if old:
                self._inventory.add(old)
            return f"{self.name} equipa {item.name} (+{item.defense_bonus} DEF)."
        if isinstance(item, Accessory):
            self._inventory.remove_at(index)
            old, self._accessory = self._accessory, item
            if old:
                self._inventory.add(old)
            return f"{self.name} equipa {item.name} ({item.describe()})."
        raise InvalidItemError("Ese objeto no se puede equipar.")

    def use_item(self, index: int, target: Optional[PartyMember] = None) -> str:
        """Usa una poción/éter sobre `target` (por defecto, el propio héroe)."""
        item = self._inventory.get(index)
        member = target or self
        if isinstance(item, Potion):
            if not member.is_alive:
                raise InvalidItemError(f"{member.name} está caído y no puede curarse.")
            self._inventory.remove_at(index)
            healed = member.heal(item.heal_amount)
            who = "" if member is self else f" en {member.name}"
            return f"{self.name} usa {item.name}{who} y recupera {healed} HP."
        if isinstance(item, Ether):
            if not member.is_alive:
                raise InvalidItemError(f"{member.name} está caído y no puede recuperar MP.")
            self._inventory.remove_at(index)
            restored = member.restore_mp(item.mp_amount)
            who = "" if member is self else f" en {member.name}"
            return f"{self.name} usa {item.name}{who} y recupera {restored} MP."
        raise InvalidItemError("Solo se pueden usar pociones y éteres.")

    # ---- serialización
    def to_dict(self) -> Dict[str, Any]:
        data = self._base_dict()
        data.update({
            "gold": self._gold,
            "floor": self._floor,
            "rooms_in_floor": self._rooms_in_floor,
            "inventory": [i.to_dict() for i in self._inventory.items],
            "weapon": self._weapon.to_dict() if self._weapon else None,
            "armor": self._armor.to_dict() if self._armor else None,
            "accessory": self._accessory.to_dict() if self._accessory else None,
            "companions": [c.to_dict() for c in self._companions],
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hero":
        hero = cls(data["name"])  # type: ignore[call-arg]
        hero._load_base(data)
        hero._gold = data["gold"]
        hero._floor = data.get("floor", 1)
        hero._rooms_in_floor = data.get("rooms_in_floor", 0)
        for raw in data.get("inventory", []):
            hero._inventory.add(item_from_dict(raw))
        if data.get("weapon"):
            hero._weapon = item_from_dict(data["weapon"])  # type: ignore[assignment]
        if data.get("armor"):
            hero._armor = item_from_dict(data["armor"])  # type: ignore[assignment]
        if data.get("accessory"):
            hero._accessory = item_from_dict(data["accessory"])  # type: ignore[assignment]
        for raw in data.get("companions", []):  # guardados viejos no lo traen
            hero._companions.append(companion_from_dict(raw))
        return hero


class Warrior(Hero):
    CLASS_KEY = "warrior"
    CLASS_NAME = "Guerrero"
    SPECIAL_NAME = "Golpe Brutal"
    GROWTH = (15, 3, 2)

    def __init__(self, name: str) -> None:
        super().__init__(name, max_hp=120, attack=12, defense=6, max_mp=20)

    def _special(self, target: Character, rng: random.Random) -> int:
        return target.take_damage(self.compute_damage(target, rng) + self.attack_power // 2)


class Mage(Hero):
    CLASS_KEY = "mage"
    CLASS_NAME = "Mago"
    SPECIAL_NAME = "Bola de Fuego (ignora defensa)"
    GROWTH = (8, 4, 1)

    def __init__(self, name: str) -> None:
        super().__init__(name, max_hp=80, attack=16, defense=3, max_mp=40)

    def _special(self, target: Character, rng: random.Random) -> int:
        return target.take_damage(self.attack_power + 6 + rng.randint(0, 3))


class Rogue(Hero):
    CLASS_KEY = "rogue"
    CLASS_NAME = "Pícaro"
    SPECIAL_NAME = "Ataque Doble"
    GROWTH = (11, 3, 1)

    def __init__(self, name: str) -> None:
        super().__init__(name, max_hp=95, attack=13, defense=4, max_mp=30)

    def _special(self, target: Character, rng: random.Random) -> int:
        return self.attack_target(target, rng) + self.attack_target(target, rng)


HERO_CLASSES = {c.CLASS_KEY: c for c in (Warrior, Mage, Rogue)}


def hero_from_dict(data: Dict[str, Any]) -> Hero:
    """Reconstruye el héroe correcto según su clase."""
    try:
        return HERO_CLASSES[data["class"]].from_dict(data)
    except (KeyError, TypeError, ValueError) as exc:
        raise SaveDataError("Datos de héroe inválidos en el guardado.") from exc


# -------------------------------------------------------------- ENEMIGOS
class Enemy(Character):
    """Criatura enemiga con recompensas y tabla de botín."""

    is_boss = False

    def __init__(
        self,
        name: str,
        max_hp: int,
        attack: int,
        defense: int,
        xp_reward: int,
        gold_reward: int,
        loot: Optional[List[Tuple[Item, float]]] = None,
        level: int = 1,
    ) -> None:
        super().__init__(name, max_hp, attack, defense, level)
        self._xp_reward = int(xp_reward)
        self._gold_reward = int(gold_reward)
        self._loot = list(loot) if loot else []

    @property
    def xp_reward(self) -> int:
        return self._xp_reward

    @property
    def gold_reward(self) -> int:
        return self._gold_reward

    @property
    def attack_power(self) -> int:
        return self._attack

    @property
    def defense_power(self) -> int:
        return self._defense

    def roll_loot(self, rng: random.Random) -> List[Item]:
        return [item for item, chance in self._loot if rng.random() < chance]


class Boss(Enemy):
    """Jefe: entra en furia con menos de la mitad de HP (+50% ataque)."""

    is_boss = True

    @property
    def enraged(self) -> bool:
        return self._hp <= self._max_hp // 2

    @property
    def attack_power(self) -> int:
        return int(self._attack * 1.5) if self.enraged else self._attack
