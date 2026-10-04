# Guía de trabajo en equipo — cómo repartir y compartir Pixel-Quest

Esta guía explica cómo hacer **entre varios** lo mismo que aquí se hizo de una vez: ampliar el juego
(compañeros, tienda, interfaz 8-bit) sin pisarse el código. La idea es simple: cada célula toca **solo su capa**,
en **su rama**, y el GitMaster integra con Pull Requests.

## 1. Quién toca qué

| Célula | Rama | Archivos que modifica | Qué entrega |
|--------|------|-----------------------|-------------|
| **1 · Dominio** | `feature/dominio` | `src/domain/models.py`, `src/domain/exceptions.py`, `tests/test_domain.py` | `PartyMember`, `Companion` (Cleric, Archer, Knight, Alchemist), `Accessory`, `Ether`, grupo del héroe (`recruit/dismiss/party`), guardado de compañeros |
| **2 · Servicios** | `feature/servicios` | `src/services/content.py` (nuevo), `src/services/app_service.py`, `tests/test_services.py` | Combate en grupo (`current_actor`, `events`), tienda por piso, `sell`, taberna (`recruit/dismiss`), posada (`rest`), más enemigos/jefes |
| **3 · Interfaz** | `feature/ui` | `src/ui/cli_interface.py`, `src/main.py`, **todo** `src/ui/gui/`, `tests/test_gui.py` | CLI actualizada + ventana 8-bit |
| **GitMaster** | `main` | `README.md`, `architecture.md`, `GUIA_EQUIPO.md` | Revisa PRs y hace los merge |

Regla de oro: **`ui → services → domain`**, nunca al revés. Por eso el orden de integración es
**Dominio → Servicios → Interfaz**: cada capa necesita que la anterior ya esté en `main`.

> Trabajo en paralelo: la célula 2 y 3 no tienen que esperar. Antes de empezar, pónganse de acuerdo en los
> *nombres* que se van a usar (el "contrato") y cada uno programa contra ese contrato:
> `Hero.party`, `Hero.recruit(c)`, `Hero.dismiss(i)`, `CombatSession.current_actor`, `CombatSession.events`,
> `GameService.tavern_offers/recruit/dismiss/sell/rest`, `shop_catalog(floor)`. Están todos en `architecture.md`.

## 2. Flujo de Git paso a paso

**Una sola vez (todos):**
```bash
git clone <URL-del-repositorio>
cd pixel-quest
```

**Cada integrante, en su célula** (ejemplo: Dominio):
```bash
git checkout main
git pull origin main                     # siempre partir de lo último
git checkout -b feature/dominio          # su rama (la crea la primera vez)

# ...programar...
python -m unittest discover -s tests -t . -v     # TODO debe pasar antes de subir

git status                               # revisar qué cambió
git add src/domain tests/test_domain.py # agregar SOLO los archivos de su capa
git commit -m "Dominio: agrega compañeros, accesorios y éter"
git push -u origin feature/dominio
```

**Abrir el Pull Request** (GitHub → "Compare & pull request"): base `main`, compare `feature/dominio`.
Usen la plantilla de `.github/pull_request_template.md`: qué cambia, cómo probarlo y captura si es visual.
Asignen como revisor al GitMaster y a **una persona de la capa vecina** (la que consume su código).

**El GitMaster** revisa, corre las pruebas y hace el merge (*Squash and merge* o *Merge commit*, pero siempre el mismo):
```bash
git checkout main
git pull origin main
git checkout feature/dominio
python -m unittest discover -s tests -t . -v
```

**Mantener la rama al día** cuando `main` avanzó (por ejemplo, Dominio ya se integró y Servicios sigue trabajando):
```bash
git checkout feature/servicios
git fetch origin
git merge origin/main                    # (o: git rebase origin/main, si el equipo ya lo usa)
python -m unittest discover -s tests -t . -v
```

## 3. Orden recomendado de PRs

1. **PR 1 — Dominio** (`feature/dominio`). Se integra primero. Las pruebas viejas deben seguir pasando (los guardados antiguos cargan sin `companions`).
2. **PR 2 — Servicios** (`feature/servicios`). Se basa en `main` ya con el dominio. Pruebas: `test_services.py`.
3. **PR 3 — Interfaz** (`feature/ui`). Se basa en `main` con servicios. Incluye consola y `src/ui/gui/`.
4. **PR 4 — Documentación** (GitMaster): `README.md`, `architecture.md`, este archivo.

## 4. Cómo evitar conflictos

- **Cada quien edita solo su carpeta.** Si necesitan algo de otra capa, pídanlo por *Issue* o mensaje; no lo editen ustedes.
- `README.md` y `architecture.md` los toca **solo el GitMaster** (son los que más chocan). Las células le mandan sus cambios en el PR.
- Commits pequeños y frecuentes; mensajes con prefijo de capa (`Dominio: ...`, `Servicios: ...`, `UI: ...`).
- Si hay conflicto al hacer `merge`: abran el archivo, busquen `<<<<<<<`, elijan/mezclen el código correcto, luego:
  ```bash
  git add <archivo>
  git commit
  ```
  y vuelvan a correr las pruebas.
- Nunca suban `data/heroes.json` (ya está en `.gitignore`): es la partida de cada persona.

## 5. Dentro de la célula 3: repartir la interfaz entre varias personas

`src/ui/gui/` está dividida en archivos independientes, ideal para repartir:

| Persona | Archivos |
|---------|----------|
| A · Arte | `sprites.py`, `backgrounds.py`, `palette.py` (dibujar personajes y fondos) |
| B · Componentes | `framebuffer.py`, `font.py`, `widgets.py`, `sound.py` |
| C · Pantallas de inicio y campamento | `screens_menu.py`, `screens_camp.py` |
| D · Combate + ventana | `screens_combat.py`, `app.py`, `tk_shell.py`, `tests/test_gui.py` |

Para ver el resultado **sin abrir la ventana**, cualquier persona puede guardar una captura:
```python
from src.ui.gui.app import GameApp
app = GameApp(servicio); app.update(0.1)
open("captura.png", "wb").write(app.render().png(2))
```

## 6. Probar lo que hicieron los demás

```bash
git fetch origin
git checkout feature/servicios      # rama de un compañero
python -m unittest discover -s tests -t . -v
python -m src.main                  # jugar con sus cambios
git checkout feature/dominio        # volver a la suya
```

## 7. Prompts sugeridos por célula (para pegar en "Prompt base usado")

**Célula 1 — Dominio.** *"Tengo un proyecto Python en capas llamado Pixel-Quest (adjunto `src/domain/models.py`). Agrega compañeros de grupo tipo Final Fantasy: una clase abstracta `PartyMember` (con MP, XP y habilidad especial) de la que hereden `Hero` y `Companion`; cuatro compañeros (Clérigo que cura a un aliado, Arquero, Caballero que se pone en guardia, Alquimista). El héroe lleva hasta 2 compañeros (`recruit`, `dismiss`, `party`). Agrega `Accessory` (bonus ATK/DEF) y `Ether` (restaura MP). Todo debe guardarse con `to_dict/from_dict` y los guardados viejos deben seguir cargando. Sin consola ni archivos en esta capa; excepciones propias; pruebas `unittest`."*

**Célula 2 — Servicios.** *"Con el dominio ya actualizado (adjunto), modifica `src/services/app_service.py`: el combate ahora es por turnos de todo el grupo (`CombatSession.current_actor`, cada acción consume el turno del miembro actual, luego ataca el enemigo a un miembro al azar) y expone `events` (texto, tipo hit/heal, objetivo, cantidad) para animar. Mueve enemigos, jefes, tienda y taberna a `content.py` como datos; la tienda se desbloquea por piso; agrega `sell`, `recruit`, `dismiss`, `rest`, trampas y más enemigos. Sin `print` ni `input`. Pruebas `unittest` de cada caso."*

**Célula 3 — Interfaz.** *"Con los servicios ya listos (adjunto), crea una interfaz gráfica de 8 bits en Python sin dependencias externas: un framebuffer de 320x240 con paleta fija y fuente bitmap propia, sprites pixel-art de 16x16 dibujados por código, ventanas azules estilo Final Fantasy y menús con cursor. Pantallas: título, crear héroe, campamento, exploración, combate en grupo, inventario, tienda, taberna y estado. Solo una capa delgada usa Tkinter; la lógica debe poder probarse sin ventana. Actualiza también la CLI para usar grupo, venta y taberna."*

**GitMaster.** *"Revisa este Pull Request: ¿respeta `ui → services → domain`?, ¿pasan todas las pruebas?, ¿toca archivos de otra capa?, ¿los mensajes de commit son claros?"*

## 8. Lista de revisión antes de abrir un PR

- [ ] `python -m unittest discover -s tests -t . -v` pasa completo.
- [ ] Solo modifiqué archivos de mi capa.
- [ ] No hay `print`/`input` en dominio ni servicios.
- [ ] No subí `data/`, `__pycache__/` ni archivos temporales.
- [ ] Probé jugando (`python -m src.main`) y adjunto captura si cambié algo visual.
