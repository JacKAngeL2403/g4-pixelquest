# Arquitectura — Pixel-Quest

```mermaid
classDiagram
    direction LR
    class Item {
        <<abstract>>
        -name
        -value
        +describe()
        +to_dict()
    }
    class Weapon { -attack_bonus }
    class Armor { -defense_bonus }
    class Accessory { -attack_bonus -defense_bonus }
    class Potion { -heal_amount }
    class Ether { -mp_amount }
    Item <|-- Weapon
    Item <|-- Armor
    Item <|-- Accessory
    Item <|-- Potion
    Item <|-- Ether

    class Inventory {
        -capacity
        -items
        +add(item)
        +get(index)
        +remove_at(index)
    }

    class Character {
        <<abstract>>
        -name
        -hp
        -max_hp
        +attack_power*
        +defense_power*
        +attack_target()
        +take_damage()
        +heal()
        +guard()
    }
    class PartyMember {
        <<abstract>>
        -mp
        -xp
        +gain_xp()
        +special_attack()
        +revive()
    }
    class Hero {
        <<abstract>>
        -gold
        -floor
        +companions
        +party
        +recruit()
        +dismiss()
        +equip()
        +use_item()
    }
    class Companion {
        <<abstract>>
        +set_level()
    }
    class Warrior
    class Mage
    class Rogue
    class Cleric
    class Archer
    class Knight
    class Alchemist
    class Enemy {
        -xp_reward
        -gold_reward
        +roll_loot()
    }
    class Boss {
        +enraged
    }
    Character <|-- PartyMember
    Character <|-- Enemy
    PartyMember <|-- Hero
    PartyMember <|-- Companion
    Hero <|-- Warrior
    Hero <|-- Mage
    Hero <|-- Rogue
    Companion <|-- Cleric
    Companion <|-- Archer
    Companion <|-- Knight
    Companion <|-- Alchemist
    Enemy <|-- Boss
    Hero *-- Inventory
    Hero o-- Weapon
    Hero o-- Armor
    Hero o-- Accessory
    Hero o-- Companion : grupo (max 2)
    Inventory o-- Item

    class DataManager {
        +load_all()
        +save_hero()
        +get_hero()
        +delete_hero()
    }
    class GameService {
        +create_hero()
        +explore()
        +start_combat()
        +finish_combat()
        +buy() +sell()
        +recruit() +dismiss()
        +rest()
    }
    class CombatSession {
        +current_actor
        +events
        +player_attack()
        +player_special()
        +player_defend()
        +player_use_item()
        +player_flee()
    }
    class MenuCLI {
        +run()
    }
    class GameApp {
        +key() +click()
        +update() +render()
    }
    class Screen {
        <<abstract>>
        +draw(framebuffer)
    }
    class Framebuffer {
        320x240 paleta fija
        +png()
    }
    class TkShell {
        ventana Tkinter
    }
    MenuCLI --> GameService
    TkShell --> GameApp
    GameApp --> Screen
    Screen --> GameService
    Screen --> Framebuffer
    GameService --> DataManager
    GameService --> CombatSession
    GameService ..> Hero
    CombatSession --> Hero
    CombatSession --> Enemy
```

## Dependencias entre capas
`ui  →  services  →  domain` (nunca al revés).

## Contenido como datos
`src/services/content.py` guarda enemigos, jefes, tienda y taberna como listas: agregar contenido no toca la lógica.

## Interfaz gráfica (`src/ui/gui/`)
El juego se dibuja en un **framebuffer de 320x240 con paleta fija** (como una consola de 8 bits) y se
amplía al mostrarlo. Solo `tk_shell.py` usa Tkinter; `GameApp` recibe teclas/clics y dibuja, por eso se
prueba sin ventana.

| Archivo | Qué hace |
|---------|----------|
| `palette.py`, `font.py` | Colores y fuente bitmap 5x7 (con tildes y Ñ) |
| `framebuffer.py` | Dibujar rectángulos, sprites, texto y exportar a PNG |
| `sprites.py` | Pixel-art de héroes, compañeros, enemigos, jefes e iconos |
| `backgrounds.py` | Campamento, título y mazmorra (5 temas por piso) |
| `widgets.py` | Ventanas azules, barras, menús con cursor y diálogos con máquina de escribir |
| `screens_menu.py` | Título, crear héroe, cargar/borrar |
| `screens_camp.py` | Campamento, exploración, inventario, tienda, taberna, estado |
| `screens_combat.py` | Combate en grupo con animaciones |
| `sound.py` | Efectos de sonido de ondas cuadradas generados por código |
| `app.py`, `tk_shell.py` | Controlador sin ventana / ventana Tkinter |
