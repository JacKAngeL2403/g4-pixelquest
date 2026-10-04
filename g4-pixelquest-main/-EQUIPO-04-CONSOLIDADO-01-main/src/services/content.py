"""Capa 2 - Contenido del juego: catálogos de enemigos, jefes, tienda y taberna.

Aquí solo hay DATOS. Para agregar un enemigo, un objeto de tienda o un compañero
nuevo basta con añadir una fila a estas listas (no hay que tocar la lógica).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from src.domain.models import Accessory, Armor, Ether, Item, Potion, Weapon

# nombre, hp, atk, def, xp, oro, piso_mínimo
ENEMY_TEMPLATES: List[Tuple[str, int, int, int, int, int, int]] = [
    ("Slime", 30, 7, 1, 15, 8, 1),
    ("Goblin", 40, 9, 2, 22, 12, 1),
    ("Murciélago", 34, 10, 1, 18, 10, 1),
    ("Esqueleto", 50, 11, 3, 30, 16, 2),
    ("Lobo Sombrío", 60, 13, 3, 38, 20, 2),
    ("Fantasma", 55, 14, 5, 44, 24, 3),
    ("Orco", 90, 16, 4, 55, 30, 3),
]

# nombre, hp, atk, def, xp, oro  (el jefe del piso N es el N-ésimo, en ciclo)
BOSS_TEMPLATES: List[Tuple[str, int, int, int, int, int]] = [
    ("Rey Slime", 120, 13, 4, 120, 80),
    ("Señor Goblin", 200, 17, 6, 200, 120),
    ("Dragón Pixelado", 320, 23, 9, 400, 250),
    ("Golem de Piedra", 420, 27, 13, 550, 320),
    ("Lich Pixelado", 520, 32, 12, 750, 450),
]


@dataclass(frozen=True)
class ShopEntry:
    item: Item
    min_floor: int = 1


def _stock() -> List[ShopEntry]:
    return [
        # Pociones y éteres
        ShopEntry(Potion("Poción Menor", 40, 15, "Cura 40 HP")),
        ShopEntry(Potion("Poción Mayor", 90, 35, "Cura 90 HP")),
        ShopEntry(Potion("Poción Superior", 180, 70, "Cura 180 HP"), 3),
        ShopEntry(Potion("Elixir de Vida", 999, 150, "Cura todo el HP"), 5),
        ShopEntry(Ether("Éter Menor", 20, 25, "Restaura 20 MP")),
        ShopEntry(Ether("Éter Mayor", 50, 60, "Restaura 50 MP"), 3),
        # Armas
        ShopEntry(Weapon("Espada de Hierro", 5, 40, "Una espada resistente")),
        ShopEntry(Weapon("Hacha de Guerra", 9, 90, "Pesada y letal")),
        ShopEntry(Weapon("Espada Rúnica", 14, 160, "Runas que brillan"), 2),
        ShopEntry(Weapon("Lanza de Mithril", 19, 260, "Ligera y afilada"), 3),
        ShopEntry(Weapon("Hoja del Alba", 26, 450, "Forjada con luz de sol"), 5),
        # Armaduras
        ShopEntry(Armor("Cota de Malla", 4, 50, "Protección media")),
        ShopEntry(Armor("Armadura de Placas", 8, 110, "Protección pesada")),
        ShopEntry(Armor("Coraza Rúnica", 12, 190, "Repele golpes"), 2),
        ShopEntry(Armor("Armadura de Mithril", 17, 300, "Casi no pesa"), 4),
        ShopEntry(Armor("Manto Estelar", 23, 480, "Tejido con estrellas"), 6),
        # Accesorios
        ShopEntry(Accessory("Anillo de Fuerza", 3, 0, 60, "+3 ATK"), 2),
        ShopEntry(Accessory("Amuleto de Hierro", 0, 3, 60, "+3 DEF"), 2),
        ShopEntry(Accessory("Brazalete Élfico", 2, 2, 100, "+2 ATK y +2 DEF"), 2),
        ShopEntry(Accessory("Capa del Viento", 4, 4, 220, "+4 ATK y +4 DEF"), 4),
    ]


def shop_entries(floor: int = 99) -> List[ShopEntry]:
    """Productos disponibles al llegar a `floor` (la tienda crece con el progreso)."""
    return [e for e in _stock() if e.min_floor <= floor]


def shop_catalog(floor: int = 99) -> List[Item]:
    """Objetos que vende la tienda para ese piso."""
    return [e.item for e in shop_entries(floor)]


def next_unlock_floor(floor: int) -> int:
    """Piso en el que la tienda tendrá productos nuevos (0 si ya está todo)."""
    later = sorted({e.min_floor for e in _stock() if e.min_floor > floor})
    return later[0] if later else 0


@dataclass(frozen=True)
class RecruitTemplate:
    name: str
    class_key: str
    base_cost: int
    blurb: str


# Compañeros disponibles en la taberna
RECRUITS: List[RecruitTemplate] = [
    RecruitTemplate("Aria", "cleric", 80, "Clériga del templo. Cura al grupo."),
    RecruitTemplate("Robin", "archer", 90, "Cazador certero. Ignora defensas."),
    RecruitTemplate("Gareth", "knight", 100, "Caballero leal. Aguanta los golpes."),
    RecruitTemplate("Zed", "alchemist", 110, "Alquimista loco. Bombas ácidas."),
]
COST_PER_LEVEL = 15  # el precio sube con el nivel del héroe
