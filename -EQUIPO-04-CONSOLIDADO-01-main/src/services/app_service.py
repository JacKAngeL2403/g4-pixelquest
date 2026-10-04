"""Capa 2 - Servicios: lógica de casos de uso (crear héroe, explorar,
combate por turnos en grupo con habilidades, tienda, taberna, inventario)."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.domain.exceptions import (
    CombatError,
    DuplicateHeroError,
    InvalidItemError,
    InventoryFullError,
    NotEnoughGoldError,
    PartyError,
    SaveDataError,
    SkillError,
)
from src.domain.models import (
    COMPANION_CLASSES,
    HERO_CLASSES,
    Boss,
    Character,
    Enemy,
    Ether,
    Hero,
    PartyMember,
    Potion,
    Scroll,
    SecretBoss,
    Weapon,
    hero_from_dict,
    item_from_dict,
)
from src.domain.skills import SKILLS, STAT_LABELS, RARE_SKILL_KEYS, Skill, SkillEffect, get_skill
from src.services.content import (
    BOSS_TEMPLATES,
    COST_PER_LEVEL,
    ENEMY_TEMPLATES,
    RECRUITS,
    SECRET_BOSSES,
    SECRET_GEAR,
    next_unlock_floor,
    secret_template,
    shop_catalog,
    shop_entries,
)
from src.services.data_manager import DataManager

ROOMS_PER_FLOOR = 4
FLEE_CHANCE = 0.5
PARTY_HP_BONUS = 0.55    # +55% de HP enemigo por cada compañero extra
SECRET_CHANCE = 0.12     # probabilidad de hallar una sala oculta por sala explorada

__all__ = [
    "CombatEvent", "CombatSession", "Event", "GameService", "RecruitOffer", "SkillOption",
    "shop_catalog", "shop_entries", "next_unlock_floor", "ROOMS_PER_FLOOR",
]


@dataclass
class Event:
    """Resultado de explorar una sala."""

    kind: str  # "combat" | "boss" | "secret" | "treasure" | "fountain" | "shrine" | "trap"
    message: str
    enemy: Optional[Enemy] = None


@dataclass
class CombatEvent:
    """Un suceso del combate. La interfaz gráfica lo usa para animar."""

    text: str
    kind: str = "info"  # "info" | "hit" | "heal" | "buff" | "debuff" | "cast"
    target: Optional[Character] = None
    amount: int = 0
    actor: Optional[Character] = None


@dataclass
class SkillOption:
    """Una habilidad en el menú de 'Habilidades' (con o sin posibilidad de usarla ahora)."""

    skill: Skill
    enabled: bool
    reason: str = ""


@dataclass
class RecruitOffer:
    """Un compañero que se puede contratar en la taberna."""

    name: str
    class_key: str
    class_name: str
    cost: int
    blurb: str
    in_party: bool
    preview: Any = None  # Companion ya subido al nivel del héroe (para mostrar sus stats)


def describe_effect(eff: SkillEffect) -> str:
    """Texto de un efecto de habilidad (para el registro de combate)."""
    name = eff.target.name
    if eff.kind == "hit":
        return f"{name} recibe {eff.amount} de daño."
    if eff.kind == "heal":
        return f"{name} recupera {eff.amount} HP."
    if eff.kind == "mp":
        return f"{name} recupera {eff.amount} MP."
    if eff.kind == "revive":
        return f"¡{name} vuelve a la vida con {eff.amount} HP!"
    sign = "sube" if eff.kind == "buff" else "baja"
    return f"{STAT_LABELS.get(eff.stat, eff.stat)} de {name} {sign} {eff.amount} por {eff.turns} turnos."


class CombatSession:
    """Combate por turnos: todo el grupo del héroe contra un enemigo.

    Cada ronda actúa, en orden, cada miembro vivo (`current_actor`) eligiendo
    Atacar, una Habilidad, Defender, un Objeto o Huir; cuando todos actuaron,
    el enemigo ataca a un miembro al azar.
    """

    def __init__(self, hero: Hero, enemy: Enemy, rng: random.Random) -> None:
        self.hero = hero
        self.enemy = enemy
        self._rng = rng
        self.turn = 1
        self.fled = False
        self.events: List[CombatEvent] = []
        self._cursor: Optional[int] = self._next_alive(0)

    # ---- estado
    @property
    def party(self) -> List[PartyMember]:
        return self.hero.party

    @property
    def party_alive(self) -> bool:
        return any(m.is_alive for m in self.party)

    @property
    def current_actor(self) -> Optional[PartyMember]:
        if self._cursor is None or self._cursor >= len(self.party):
            return None
        return self.party[self._cursor]

    @property
    def is_over(self) -> bool:
        return self.fled or not self.party_alive or not self.enemy.is_alive

    @property
    def victory(self) -> bool:
        return self.party_alive and not self.enemy.is_alive

    def _next_alive(self, start: int) -> Optional[int]:
        for i in range(start, len(self.party)):
            if self.party[i].is_alive:
                return i
        return None

    def _emit(self, text: str, kind: str = "info", target: Optional[Character] = None,
              amount: int = 0, actor: Optional[Character] = None) -> None:
        self.events.append(CombatEvent(text, kind, target, amount, actor))

    # ---- menú de habilidades
    def skill_options(self) -> List[SkillOption]:
        """Habilidades del miembro actual, indicando cuáles puede usar ahora y por qué no."""
        actor = self.current_actor
        if actor is None:
            return []
        out = []
        for skill in actor.skills:
            if actor.mp < skill.cost:
                out.append(SkillOption(skill, False, "MP insuficiente"))
            elif not skill.has_valid_target(actor, self.party):
                reason = "Nadie caído" if skill.target == "fallen" else "Nadie lo necesita"
                out.append(SkillOption(skill, False, reason))
            else:
                out.append(SkillOption(skill, True))
        return out

    def skill_targets(self, skill_key: str) -> List[int]:
        """Índices del grupo a los que se puede lanzar la habilidad (si apunta a un aliado)."""
        actor = self.current_actor
        skill = get_skill(skill_key)
        if actor is None or skill.target not in ("ally", "fallen"):
            return []
        return skill.valid_ally_targets(actor, self.party)

    # ---- flujo de turnos
    def _act(self, action) -> List[str]:
        """Ejecuta `action(actor)`; luego avanza al siguiente miembro / turno enemigo."""
        if self.is_over:
            raise CombatError("El combate ya terminó.")
        actor = self.current_actor
        if actor is None:
            raise CombatError("No hay nadie que pueda actuar.")
        self.events = []
        action(actor)  # puede lanzar un error ANTES de cambiar nada
        self._after_action()
        return [e.text for e in self.events]

    def _after_action(self) -> None:
        if self.fled:
            return
        if not self.enemy.is_alive:
            self._emit(f"¡{self.enemy.name} ha sido derrotado!")
            return
        assert self._cursor is not None
        nxt = self._next_alive(self._cursor + 1)
        if nxt is not None:
            self._cursor = nxt
            return
        self._enemy_turn()
        self._end_round()

    def _enemy_turn(self) -> None:
        living = [m for m in self.party if m.is_alive]
        target = self._rng.choice(living)
        was_enraged = getattr(self.enemy, "enraged", False)
        dmg = self.enemy.attack_target(target, self._rng)
        if was_enraged:
            self._emit(f"¡{self.enemy.name} está furioso!")
        self._emit(f"{self.enemy.name} ataca y causa {dmg} de daño a {target.name}.",
                   "hit", target, dmg, self.enemy)
        if not target.is_alive:
            self._emit(f"{target.name} ha caído en combate...")

    def _end_round(self) -> None:
        for m in self.party:
            if m.is_alive:
                m.regen_mp(2)
            m.tick_mods()
        self.enemy.tick_mods()
        self.turn += 1
        self._cursor = self._next_alive(0)

    # ---- acciones del jugador (las ejecuta el miembro actual)
    def player_attack(self) -> List[str]:
        def action(actor: PartyMember) -> None:
            actor.stop_guard()
            dmg = actor.attack_target(self.enemy, self._rng)
            self._emit(f"{actor.name} ataca a {self.enemy.name} y causa {dmg} de daño.",
                       "hit", self.enemy, dmg, actor)
        return self._act(action)

    def player_skill(self, skill_key: str, target_index: Optional[int] = None) -> List[str]:
        """Usa una habilidad conocida. Si apunta a un aliado, `target_index` es su posición en el grupo."""
        def action(actor: PartyMember) -> None:
            skill = get_skill(skill_key)
            ally = None
            if skill.target in ("ally", "fallen"):
                if target_index is None or not 0 <= target_index < len(self.party):
                    raise SkillError("Elige a un aliado.")
                ally = self.party[target_index]
            actor.stop_guard()
            effects = actor.use_skill(skill_key, self.enemy, self.party, ally, self._rng)
            self._emit(f"{actor.name} usa {skill.name}.", "cast", actor, 0, actor)
            self._report(effects, actor)
        return self._act(action)

    def _report(self, effects: List[SkillEffect], actor: Character) -> None:
        """Convierte los efectos de una habilidad en eventos (agrupa golpes seguidos)."""
        i = 0
        while i < len(effects):
            eff = effects[i]
            if eff.kind == "hit":
                total, hits = eff.amount, 1
                while i + 1 < len(effects) and effects[i + 1].kind == "hit" and effects[i + 1].target is eff.target:
                    i += 1
                    total += effects[i].amount
                    hits += 1
                text = f"{eff.target.name} recibe {total} de daño" + (f" ({hits} golpes)." if hits > 1 else ".")
                self._emit(text, "hit", eff.target, total, actor)
            else:
                kind = {"heal": "heal", "mp": "heal", "revive": "heal"}.get(eff.kind, eff.kind)
                amount = eff.amount if eff.kind in ("heal", "revive") else 0
                self._emit(describe_effect(eff), kind, eff.target, amount, actor)
            i += 1

    def player_defend(self) -> List[str]:
        def action(actor: PartyMember) -> None:
            actor.stop_guard()
            actor.guard()
            self._emit(f"{actor.name} se pone en guardia (recibirá la mitad de daño).")
        return self._act(action)

    def player_use_item(self, index: int, target_index: Optional[int] = None) -> List[str]:
        """Usa una poción/éter del inventario sobre un miembro (por defecto, quien actúa)."""
        def action(actor: PartyMember) -> None:
            target = actor
            if target_index is not None:
                if not 0 <= target_index < len(self.party):
                    raise CombatError("Ese aliado no existe.")
                target = self.party[target_index]
            item = self.hero.inventory.get(index)
            if isinstance(item, Scroll):
                raise InvalidItemError("Los pergaminos se leen fuera del combate.")
            before = target.hp
            actor.stop_guard()
            text = self.hero.use_item(index, target)  # puede lanzar InvalidItemError
            gained = target.hp - before
            self._emit(text, "heal" if gained > 0 else "info", target, max(0, gained), actor)
        return self._act(action)

    player_use_potion = player_use_item  # nombre anterior, se mantiene por compatibilidad

    def player_flee(self) -> List[str]:
        def action(actor: PartyMember) -> None:
            if self.enemy.is_boss:
                raise CombatError("¡No puedes huir de un jefe!")
            actor.stop_guard()
            if self._rng.random() < FLEE_CHANCE:
                self.fled = True
                self._emit(f"{self.hero.name} y su grupo logran escapar.")
            else:
                self._emit("No lograste escapar...")
        return self._act(action)


class GameService:
    """Fachada de la lógica del juego para la capa de interfaz."""

    def __init__(self, data_manager: DataManager, rng: Optional[random.Random] = None) -> None:
        self._data = data_manager
        self._rng = rng or random.Random()

    # ---------------------------------------------------------- héroes
    @staticmethod
    def available_classes() -> List[Hero]:
        """Instancias de muestra para mostrar stats base en el menú."""
        return [cls("Muestra") for cls in HERO_CLASSES.values()]

    def create_hero(self, name: str, class_key: str) -> Hero:
        hero = HERO_CLASSES[class_key](name)  # valida el nombre
        if self._data.exists(hero.name):
            raise DuplicateHeroError(f"Ya existe un héroe llamado '{hero.name}'.")
        hero.inventory.add(Potion("Poción Menor", 40, 15, "Cura 40 HP"))
        self.save_hero(hero)
        return hero

    def save_hero(self, hero: Hero) -> None:
        self._data.save_hero(hero.name, hero.to_dict())

    def load_hero(self, name: str) -> Hero:
        return hero_from_dict(self._data.get_hero(name))

    def delete_hero(self, name: str) -> None:
        self._data.delete_hero(name)

    def list_heroes(self) -> List[str]:
        return self._data.list_names()

    def list_summaries(self) -> List[Dict[str, Any]]:
        """Datos resumidos de cada partida (para la pantalla 'Continuar')."""
        summaries = []
        for name in self.list_heroes():
            try:
                hero = self.load_hero(name)
            except (SaveDataError, PartyError):
                continue  # partida dañada: se omite
            summaries.append({
                "name": hero.name, "class_key": hero.CLASS_KEY, "class_name": hero.CLASS_NAME,
                "level": hero.level, "floor": hero.floor, "companions": len(hero.companions),
                "secrets": len(hero.secrets),
            })
        return summaries

    # ------------------------------------------------------ exploración
    def _scale(self, floor: int) -> float:
        return 1 + 0.25 * (floor - 1)

    @staticmethod
    def _party_hp_factor(party_size: int) -> float:
        return 1 + PARTY_HP_BONUS * max(0, party_size - 1)

    def _spawn_enemy(self, floor: int, party_size: int = 1) -> Enemy:
        pool = [t for t in ENEMY_TEMPLATES if t[6] <= floor]
        name, hp, atk, dfn, xp, gold, _ = self._rng.choice(pool)
        k = self._scale(floor)
        loot = [(Potion("Poción Menor", 40, 15, "Cura 40 HP"), 0.35),
                (Ether("Éter Menor", 20, 25, "Restaura 20 MP"), 0.12),
                (Weapon("Daga Oxidada", 3, 10, "Mejor que nada"), 0.10)]
        return Enemy(name, int(hp * k * self._party_hp_factor(party_size)), int(atk * k),
                     int(dfn * k), int(xp * k), int(gold * k), loot, level=floor)

    def _spawn_boss(self, floor: int, party_size: int = 1, hero: Optional[Hero] = None) -> Boss:
        name, hp, atk, dfn, xp, gold = BOSS_TEMPLATES[(floor - 1) % len(BOSS_TEMPLATES)]
        if floor > len(BOSS_TEMPLATES):
            name = f"{name} Nv{floor}"
        k = self._scale(floor)
        loot = [(Weapon(f"Espada del Jefe +{floor}", 6 + 2 * floor, 60, "Botín de jefe"), 1.0),
                (Potion("Poción Mayor", 90, 35, "Cura 90 HP"), 1.0),
                (Ether("Éter Mayor", 50, 60, "Restaura 50 MP"), 0.5)]
        scroll = self.random_scroll(hero) if hero else None
        if scroll is not None:
            loot.append((scroll, 0.6))
        return Boss(name, int(hp * k * self._party_hp_factor(party_size)), int(atk * k),
                    int(dfn * k), int(xp * k), int(gold * k), loot, level=floor)

    def spawn_secret_boss(self, key: str, floor: int, party_size: int = 1) -> SecretBoss:
        tpl = secret_template(key)
        k = self._scale(max(1, floor - tpl.min_floor + 1)) * 1.0
        loot = [(SECRET_GEAR[key](), 1.0), (Scroll(tpl.reward_scroll, 200), 1.0),
                (Potion("Poción Mayor", 90, 35, "Cura 90 HP"), 1.0)]
        return SecretBoss(tpl.key, tpl.art_key, tpl.name, int(tpl.hp * k * self._party_hp_factor(party_size)),
                          int(tpl.atk * k), int(tpl.defense * k), int(tpl.xp * k), int(tpl.gold * k),
                          loot, level=floor)

    # ---- aprendizaje de habilidades
    def random_scroll(self, hero: Optional[Hero]) -> Optional[Scroll]:
        """Un pergamino de una habilidad que alguien del grupo todavía pueda aprender."""
        if hero is None:
            return None
        pool = sorted({s.key for m in hero.party for s in m.learnable_skills()})
        if not pool:
            return None
        key = self._rng.choice(pool)
        return Scroll(key, max(60, get_skill(key).cost * 8))

    def _shrine(self, hero: Hero) -> Event:
        """Un santuario antiguo enseña una habilidad a alguien del grupo."""
        candidates = [(m, s) for m in hero.party if m.is_alive for s in m.learnable_skills()]
        if not candidates:
            gold = 40 * hero.floor
            hero.earn_gold(gold)
            return Event("shrine", f"Un santuario antiguo brilla, pero ya no tiene nada que enseñarte. "
                                   f"Dejas una ofrenda y recibes {gold} de oro.")
        member, skill = self._rng.choice(candidates)
        member.learn_skill(skill.key)
        return Event("shrine", f"Un santuario antiguo susurra un secreto. ¡{member.name} aprende {skill.name}!")

    def _secret_candidates(self, hero: Hero):
        return [t for t in SECRET_BOSSES if t.min_floor <= hero.floor and t.key not in hero.secrets]

    def explore(self, hero: Hero) -> Event:
        size = len(hero.party)
        if hero.rooms_in_floor >= ROOMS_PER_FLOOR:
            boss = self._spawn_boss(hero.floor, size, hero)
            return Event("boss", f"¡La puerta del jefe se abre! {boss.name} bloquea tu camino.", boss)
        candidates = self._secret_candidates(hero)
        if candidates and self._rng.random() < SECRET_CHANCE:
            tpl = self._rng.choice(candidates)
            return Event("secret", tpl.intro, self.spawn_secret_boss(tpl.key, hero.floor, size))
        hero.advance_room()
        roll = self._rng.random()
        if roll < 0.50:
            enemy = self._spawn_enemy(hero.floor, size)
            return Event("combat", f"Un {enemy.name} aparece de entre las sombras.", enemy)
        if roll < 0.66:
            gold = self._rng.randint(10, 25) * hero.floor
            hero.earn_gold(gold)
            text = f"Encuentras un cofre con {gold} de oro."
            found = self.random_scroll(hero) if self._rng.random() < 0.25 else None
            if found is None and self._rng.random() < 0.4:
                found = Potion("Poción Menor", 40, 15, "Cura 40 HP")
            if found is not None:
                try:
                    hero.inventory.add(found)
                    text += f" ¡Y {found.name}!"
                except InventoryFullError:
                    text += f" Había {found.name}, pero tu inventario está lleno."
            return Event("treasure", text)
        if roll < 0.78:
            healed = 0
            for member in hero.party:
                if member.is_alive:
                    healed += member.heal(int(member.max_hp * 0.3))
                    member.restore_mp(member.max_mp)
            return Event("fountain", f"Una fuente mágica cura a tu grupo ({healed} HP) y restaura su MP.")
        if roll < 0.90:
            return self._shrine(hero)
        # trampa: daña a todos pero nunca mata
        total = 0
        for member in hero.party:
            if member.is_alive:
                dmg = min(max(1, int(member.max_hp * 0.08)) * hero.floor, member.hp - 1)
                total += member.take_damage(max(0, dmg))
        return Event("trap", f"¡Una trampa de pinchos! El grupo pierde {total} HP en total.")

    # ---------------------------------------------------------- combate
    def start_combat(self, hero: Hero, enemy: Enemy) -> CombatSession:
        return CombatSession(hero, enemy, self._rng)

    def finish_combat(self, session: CombatSession) -> List[str]:
        hero, enemy = session.hero, session.enemy
        msgs: List[str] = []
        if session.fled:
            msgs.append("Vuelves a la sala anterior.")
        elif session.victory:
            hero.earn_gold(enemy.gold_reward)
            msgs.append(f"¡Victoria! Ganas {enemy.xp_reward} XP y {enemy.gold_reward} de oro.")
            for member in hero.party:
                if member.is_alive and member.gain_xp(enemy.xp_reward):
                    msgs.append(f"¡{member.name} SUBE A NIVEL {member.level}! HP y MP restaurados.")
                for skill in member.pop_new_skills():
                    msgs.append(f"¡{member.name} aprende {skill.name}!")
            for item in enemy.roll_loot(self._rng):
                try:
                    hero.inventory.add(item_from_dict(item.to_dict()))
                    msgs.append(f"Botín: {item.name} ({item.describe()}).")
                except InventoryFullError:
                    msgs.append(f"No cabe {item.name} en tu inventario y lo dejas atrás.")
            if enemy.is_boss and getattr(enemy, "is_secret", False):
                hero.defeat_secret(enemy.secret_key)
                msgs.append(f"¡Has derrotado a un jefe secreto: {enemy.name}!")
            elif enemy.is_boss:
                hero.next_floor()
                msgs.append(f"¡Derrotaste al jefe! Avanzas al piso {hero.floor}.")
        else:
            lost = hero.revive_after_defeat()
            for companion in hero.companions:
                companion.revive(0.5)
                companion.restore_mp(companion.max_mp)
            msgs.append(f"Has sido derrotado. Despiertas en el campamento y pierdes {lost} de oro.")
        for member in hero.party:  # los caídos se levantan con 25% de HP; los efectos temporales terminan
            member.clear_mods()
            if not member.is_alive:
                member.revive(0.25)
                msgs.append(f"{member.name} se levanta, malherido.")
        self.save_hero(hero)
        return msgs

    # ----------------------------------------------- habilidades fuera de combate
    @staticmethod
    def castable_skills(member: PartyMember, party: List[PartyMember]) -> List[SkillOption]:
        """Habilidades de `member` que sirven fuera del combate (curar, revivir, dar MP)."""
        out = []
        for skill in member.skills:
            if not skill.usable_outside_combat:
                continue
            if member.mp < skill.cost:
                out.append(SkillOption(skill, False, "MP insuficiente"))
            elif not skill.has_valid_target(member, party):
                out.append(SkillOption(skill, False, "Nadie lo necesita"))
            else:
                out.append(SkillOption(skill, True))
        return out

    def cast_skill(self, hero: Hero, caster_index: int, skill_key: str,
                   target_index: Optional[int] = None) -> List[str]:
        """Usa una habilidad de curación/revivir/MP fuera del combate."""
        party = hero.party
        if not 0 <= caster_index < len(party):
            raise PartyError("Ese miembro del grupo no existe.")
        caster = party[caster_index]
        skill = get_skill(skill_key)
        if not skill.usable_outside_combat:
            raise SkillError(f"{skill.name} solo se puede usar en combate.")
        if not caster.is_alive:
            raise CombatError(f"{caster.name} está caído.")
        ally = None
        if skill.target in ("ally", "fallen"):
            if target_index is None or not 0 <= target_index < len(party):
                raise SkillError("Elige a un aliado.")
            ally = party[target_index]
        effects = caster.use_skill(skill_key, None, party, ally, self._rng)
        self.save_hero(hero)
        return [f"{caster.name} usa {skill.name}."] + [describe_effect(e) for e in effects]

    # ---------------------------------------------------- tienda / items
    @staticmethod
    def shop_items(hero: Hero):
        return shop_catalog(hero.floor)

    def buy(self, hero: Hero, catalog_index: int) -> str:
        catalog = shop_catalog(hero.floor)
        if not 0 <= catalog_index < len(catalog):
            raise InvalidItemError("Ese producto no existe.")
        item = catalog[catalog_index]
        if hero.gold < item.value:
            hero.spend_gold(item.value)  # lanza NotEnoughGoldError
        hero.inventory.add(item_from_dict(item.to_dict()))  # lanza InventoryFullError
        hero.spend_gold(item.value)
        self.save_hero(hero)
        return f"Compraste {item.name} por {item.value} de oro."

    @staticmethod
    def sell_price(item) -> int:
        return item.value // 2

    def sell(self, hero: Hero, index: int) -> str:
        item = hero.inventory.remove_at(index)
        price = self.sell_price(item)
        hero.earn_gold(price)
        self.save_hero(hero)
        return f"Vendiste {item.name} por {price} de oro."

    def equip(self, hero: Hero, index: int) -> str:
        msg = hero.equip(index)
        self.save_hero(hero)
        return msg

    def use_item(self, hero: Hero, index: int, member_index: int = 0) -> str:
        """Usa un objeto fuera de combate sobre un miembro del grupo (0 = héroe)."""
        party = hero.party
        if not 0 <= member_index < len(party):
            raise PartyError("Ese miembro del grupo no existe.")
        msg = hero.use_item(index, party[member_index])
        self.save_hero(hero)
        return msg

    def drop_item(self, hero: Hero, index: int) -> str:
        item = hero.inventory.remove_at(index)
        self.save_hero(hero)
        return f"Tiraste {item.name}."

    # ------------------------------------------------------------ taberna
    def tavern_offers(self, hero: Hero) -> List[RecruitOffer]:
        offers = []
        in_party = {c.name.lower() for c in hero.companions}
        for tpl in RECRUITS:
            cls = COMPANION_CLASSES[tpl.class_key]
            cost = tpl.base_cost + COST_PER_LEVEL * (hero.level - 1)
            offers.append(RecruitOffer(tpl.name, tpl.class_key, cls.CLASS_NAME, cost, tpl.blurb,
                                       tpl.name.lower() in in_party,
                                       self._make_companion(tpl.class_key, tpl.name, hero.level)))
        return offers

    @staticmethod
    def _make_companion(class_key: str, name: str, level: int):
        companion = COMPANION_CLASSES[class_key](name)
        companion.set_level(level)
        return companion

    def recruit(self, hero: Hero, offer_index: int) -> str:
        offers = self.tavern_offers(hero)
        if not 0 <= offer_index < len(offers):
            raise PartyError("Ese aventurero no existe.")
        offer = offers[offer_index]
        if offer.in_party:
            raise PartyError(f"{offer.name} ya está en tu grupo.")
        companion = self._make_companion(offer.class_key, offer.name, hero.level)
        hero.recruit(companion)  # lanza PartyFullError
        try:
            hero.spend_gold(offer.cost)  # lanza NotEnoughGoldError
        except NotEnoughGoldError:
            hero.dismiss(len(hero.companions) - 1)  # deshace el reclutamiento
            raise
        self.save_hero(hero)
        return f"¡{offer.name} el {offer.class_name} se une a tu grupo!"

    def dismiss(self, hero: Hero, companion_index: int) -> str:
        companion = hero.dismiss(companion_index)
        self.save_hero(hero)
        return f"{companion.name} se despide y vuelve a la taberna."

    # ------------------------------------------------------------- posada
    @staticmethod
    def inn_price(hero: Hero) -> int:
        return 10 * hero.level

    def rest(self, hero: Hero) -> str:
        price = self.inn_price(hero)
        hero.spend_gold(price)  # lanza NotEnoughGoldError
        for member in hero.party:
            member.revive(1.0)
            member.heal(member.max_hp)
            member.restore_mp(member.max_mp)
        self.save_hero(hero)
        return f"Descansas en la posada por {price} de oro. ¡Todo el grupo recupera HP y MP!"
