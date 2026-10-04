"""Capa 3 - Presentación (modo consola). No contiene reglas del juego."""
from __future__ import annotations

from typing import List, Optional

from src.domain.exceptions import PixelQuestError
from src.domain.models import Enemy, Ether, Hero, PartyMember, Potion
from src.services.app_service import CombatSession, GameService, next_unlock_floor, shop_catalog

LINE = "=" * 60


def bar(current: int, maximum: int, width: int = 20, fill: str = "#") -> str:
    ratio = 0 if maximum <= 0 else max(0, min(1, current / maximum))
    filled = round(ratio * width)
    return "[" + fill * filled + "." * (width - filled) + f"] {current}/{maximum}"


class MenuCLI:
    def __init__(self, service: GameService) -> None:
        self._service = service

    # ----------------------------------------------------------- helpers
    @staticmethod
    def _ask_text(prompt: str) -> str:
        return input(prompt).strip()

    @staticmethod
    def _ask_int(prompt: str, low: int, high: int) -> int:
        while True:
            raw = input(prompt).strip()
            if raw.lstrip("-").isdigit() and low <= int(raw) <= high:
                return int(raw)
            print(f"  Ingresa un número entre {low} y {high}.")

    @staticmethod
    def _print_all(lines) -> None:
        for line in lines:
            print("  " + line)

    # ------------------------------------------------------------- flujo
    def run(self) -> None:
        print(LINE)
        print("      PIXEL-QUEST  -  Motor RPG en consola")
        print(LINE)
        try:
            self._main_menu()
        except (KeyboardInterrupt, EOFError):
            print("\n¡Hasta pronto, aventurero!")

    def _main_menu(self) -> None:
        while True:
            print("\n--- MENÚ PRINCIPAL ---")
            print("1) Crear héroe\n2) Cargar héroe\n3) Ver héroes guardados\n4) Borrar héroe\n0) Salir")
            option = self._ask_int("> ", 0, 4)
            try:
                if option == 0:
                    print("¡Hasta pronto, aventurero!")
                    return
                if option == 1:
                    self._create_hero()
                elif option == 2:
                    hero = self._choose_saved_hero()
                    if hero:
                        self._hero_menu(hero)
                elif option == 3:
                    for s in self._service.list_summaries():
                        print(f"  {s['name']:<20} {s['class_name']:<9} Nv{s['level']} "
                              f"piso {s['floor']}  compañeros: {s['companions']}")
                    if not self._service.list_heroes():
                        print("  (ninguno)")
                elif option == 4:
                    name = self._ask_text("Nombre del héroe a borrar: ")
                    self._service.delete_hero(name)
                    print("Héroe eliminado.")
            except PixelQuestError as err:
                print(f"  ! {err}")

    def _create_hero(self) -> None:
        name = self._ask_text("Nombre de tu héroe: ")
        classes = self._service.available_classes()
        print("\nElige tu clase:")
        for i, h in enumerate(classes, 1):
            print(f"{i}) {h.CLASS_NAME:<9} HP {h.max_hp:>3} | ATK {h.attack_power:>2} | "
                  f"DEF {h.defense_power} | MP {h.max_mp} | Especial: {h.SPECIAL_NAME}")
        choice = self._ask_int("> ", 1, len(classes))
        hero = self._service.create_hero(name, classes[choice - 1].CLASS_KEY)
        print(f"¡{hero.name} el {hero.CLASS_NAME} ha nacido!")
        self._hero_menu(hero)

    def _choose_saved_hero(self) -> Optional[Hero]:
        names = self._service.list_heroes()
        if not names:
            print("No hay héroes guardados.")
            return None
        for i, n in enumerate(names, 1):
            print(f"{i}) {n}")
        return self._service.load_hero(names[self._ask_int("> ", 1, len(names)) - 1])

    # ---------------------------------------------------------- héroe
    def _hero_menu(self, hero: Hero) -> None:
        while True:
            print(f"\n--- {hero.name} | Piso {hero.floor} | Oro {hero.gold} ---")
            print("1) Explorar\n2) Inventario\n3) Tienda\n4) Taberna (compañeros)\n"
                  f"5) Posada ({self._service.inn_price(hero)} oro)\n6) Estado\n7) Guardar\n0) Volver")
            option = self._ask_int("> ", 0, 7)
            try:
                if option == 0:
                    self._service.save_hero(hero)
                    print("Partida guardada.")
                    return
                if option == 1:
                    self._explore(hero)
                elif option == 2:
                    self._inventory_menu(hero)
                elif option == 3:
                    self._shop_menu(hero)
                elif option == 4:
                    self._tavern_menu(hero)
                elif option == 5:
                    print(self._service.rest(hero))
                elif option == 6:
                    self._show_status(hero)
                elif option == 7:
                    self._service.save_hero(hero)
                    print("Partida guardada.")
            except PixelQuestError as err:
                print(f"  ! {err}")

    def _show_status(self, hero: Hero) -> None:
        print(f"\n{LINE}")
        for m in hero.party:
            print(f"{m.name} - {m.CLASS_NAME} Nv{m.level}" + ("  (CAÍDO)" if not m.is_alive else ""))
            print(f"  HP  {bar(m.hp, m.max_hp)}")
            print(f"  MP  {bar(m.mp, m.max_mp, fill='*')}")
            print(f"  XP  {bar(m.xp, m.xp_to_next, fill='+')}")
            print(f"  ATK {m.attack_power} | DEF {m.defense_power}")
        print(f"Oro {hero.gold}")
        print(f"Arma: {hero.weapon.name if hero.weapon else '-'} | "
              f"Armadura: {hero.armor.name if hero.armor else '-'} | "
              f"Accesorio: {hero.accessory.name if hero.accessory else '-'}")
        print(f"Progreso: piso {hero.floor}, sala {hero.rooms_in_floor}/4\n{LINE}")

    # ------------------------------------------------------ exploración
    def _explore(self, hero: Hero) -> None:
        event = self._service.explore(hero)
        print(f"\n>> {event.message}")
        if event.enemy is not None:
            self._combat(hero, event.enemy)

    def _pick_member(self, hero: Hero, prompt: str = "¿A quién?") -> Optional[int]:
        party = hero.party
        print(prompt)
        for n, m in enumerate(party, 1):
            print(f"{n}) {m.name:<12} HP {m.hp}/{m.max_hp}  MP {m.mp}/{m.max_mp}"
                  + ("  (caído)" if not m.is_alive else ""))
        print("0) Cancelar")
        choice = self._ask_int("> ", 0, len(party))
        return None if choice == 0 else choice - 1

    def _combat(self, hero: Hero, enemy: Enemy) -> None:
        session = self._service.start_combat(hero, enemy)
        while not session.is_over:
            actor = session.current_actor
            assert actor is not None
            self._show_combat(session)
            print(f"Turno de {actor.name} ({actor.CLASS_NAME})")
            print(f"1) Atacar\n2) {actor.SPECIAL_NAME} ({actor.SPECIAL_COST} MP)\n"
                  "3) Defender\n4) Objeto\n5) Huir")
            option = self._ask_int("> ", 1, 5)
            try:
                if option == 1:
                    lines = session.player_attack()
                elif option == 2:
                    lines = session.player_special()
                elif option == 3:
                    lines = session.player_defend()
                elif option == 4:
                    picked = self._pick_usable(hero)
                    if picked is None:
                        continue
                    target = self._pick_member(hero, "¿Sobre quién?")
                    if target is None:
                        continue
                    lines = session.player_use_item(picked, target)
                else:
                    lines = session.player_flee()
                self._print_all(lines)
            except PixelQuestError as err:
                print(f"  ! {err}")
        print()
        self._print_all(self._service.finish_combat(session))

    def _show_combat(self, s: CombatSession) -> None:
        print(f"\n--- Turno {s.turn} ---")
        print(f"{s.enemy.name:<16} {bar(s.enemy.hp, s.enemy.max_hp, fill='#')}")
        for m in s.party:
            mark = ">" if m is s.current_actor else " "
            print(f"{mark}{m.name:<15} {bar(m.hp, m.max_hp)}  MP {m.mp}")

    def _pick_usable(self, hero: Hero) -> Optional[int]:
        usable = [(i, it) for i, it in enumerate(hero.inventory.items)
                  if isinstance(it, (Potion, Ether))]
        if not usable:
            print("  No tienes pociones ni éteres.")
            return None
        for n, (_, it) in enumerate(usable, 1):
            print(f"{n}) {it.name} ({it.describe()})")
        print("0) Cancelar")
        choice = self._ask_int("> ", 0, len(usable))
        return None if choice == 0 else usable[choice - 1][0]

    # -------------------------------------------------------- inventario
    def _print_inventory(self, hero: Hero) -> None:
        inv = hero.inventory
        print(f"\nInventario ({len(inv)}/{inv.capacity}):")
        if not len(inv):
            print("  (vacío)")
        for i, it in enumerate(inv.items, 1):
            print(f"  {i}) {it.name:<22} {it.describe()}")

    def _inventory_menu(self, hero: Hero) -> None:
        while True:
            self._print_inventory(hero)
            print("1) Equipar\n2) Usar objeto\n3) Tirar objeto\n0) Volver")
            option = self._ask_int("> ", 0, 3)
            if option == 0 or not len(hero.inventory):
                return
            number = self._ask_int("Número de objeto: ", 1, len(hero.inventory)) - 1
            try:
                if option == 1:
                    print(self._service.equip(hero, number))
                elif option == 2:
                    target = self._pick_member(hero, "¿Sobre quién?")
                    if target is not None:
                        print(self._service.use_item(hero, number, target))
                else:
                    print(self._service.drop_item(hero, number))
            except PixelQuestError as err:
                print(f"  ! {err}")

    # ------------------------------------------------------------ tienda
    def _shop_menu(self, hero: Hero) -> None:
        while True:
            catalog = shop_catalog(hero.floor)
            print(f"\n--- TIENDA (tu oro: {hero.gold}) ---")
            for i, it in enumerate(catalog, 1):
                print(f"{i:>2}) {it.name:<22} {it.describe():<28} {it.value} oro")
            print(" v) Vender objetos   0) Salir")
            unlock = next_unlock_floor(hero.floor)
            if unlock:
                print(f"  (Productos nuevos al llegar al piso {unlock})")
            raw = input("> ").strip().lower()
            if raw == "0":
                return
            try:
                if raw == "v":
                    self._sell_menu(hero)
                elif raw.isdigit() and 1 <= int(raw) <= len(catalog):
                    print(self._service.buy(hero, int(raw) - 1))
                else:
                    print(f"  Ingresa un número entre 0 y {len(catalog)}, o 'v'.")
            except PixelQuestError as err:
                print(f"  ! {err}")

    def _sell_menu(self, hero: Hero) -> None:
        if not len(hero.inventory):
            print("  No tienes nada que vender.")
            return
        self._print_inventory(hero)
        for i, it in enumerate(hero.inventory.items, 1):
            print(f"  {i}) {it.name:<22} se paga {self._service.sell_price(it)} oro")
        number = self._ask_int("Número a vender (0 cancelar): ", 0, len(hero.inventory))
        if number:
            print(self._service.sell(hero, number - 1))

    # ----------------------------------------------------------- taberna
    def _tavern_menu(self, hero: Hero) -> None:
        while True:
            print(f"\n--- TABERNA (tu oro: {hero.gold}) ---")
            print("Tu grupo: " + ", ".join(f"{m.name} ({m.CLASS_NAME} Nv{m.level})" for m in hero.party))
            offers = self._service.tavern_offers(hero)
            for i, o in enumerate(offers, 1):
                state = "en tu grupo" if o.in_party else f"{o.cost} oro"
                print(f"{i}) {o.name:<8} {o.class_name:<10} {state:<12} {o.blurb}")
            print("d) Despedir a un compañero   0) Salir")
            raw = input("> ").strip().lower()
            if raw == "0":
                return
            try:
                if raw == "d":
                    if not hero.companions:
                        print("  No tienes compañeros.")
                        continue
                    for n, c in enumerate(hero.companions, 1):
                        print(f"{n}) {c.name}")
                    n = self._ask_int("Número (0 cancelar): ", 0, len(hero.companions))
                    if n:
                        print(self._service.dismiss(hero, n - 1))
                elif raw.isdigit() and 1 <= int(raw) <= len(offers):
                    print(self._service.recruit(hero, int(raw) - 1))
                else:
                    print(f"  Ingresa un número entre 0 y {len(offers)}, o 'd'.")
            except PixelQuestError as err:
                print(f"  ! {err}")
