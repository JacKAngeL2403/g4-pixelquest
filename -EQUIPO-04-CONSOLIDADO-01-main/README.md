# Pixel-Quest — RPG de mazmorras con interfaz 8-bit

Juego RPG en Python (Arquitectura en Capas + POO). Crea un héroe (Guerrero, Mago, Pícaro),
**recluta compañeros** (Clérigo, Arquero, Caballero, Alquimista) y baja por los pisos de la
mazmorra con **combates por turnos en grupo**, al estilo Final Fantasy. Incluye tienda que crece
con el progreso, venta de objetos, posada y jefes por piso.

Tiene **dos interfaces** sobre la misma lógica: una ventana gráfica de 8 bits y la consola original.

## Ejecutar
```bash
python -m src.main            # interfaz gráfica 8-bit (por defecto)
python -m src.main --cli      # versión de consola
python -m src.main --scale 3  # tamaño de ventana (2, 3 o 4)
```
Ejecutar siempre desde la raíz del proyecto. Requiere **Python 3.9+** y **sin instalar nada**:
la ventana usa Tkinter (incluido con Python en Windows y macOS; en Linux: `sudo apt install python3-tk`).
Si Tkinter no existe, el juego abre la versión de consola automáticamente.

### Controles de la ventana
| Acción | Teclado | Mouse |
|--------|---------|-------|
| Mover cursor | Flechas o W/A/S/D | Pasar el mouse |
| Aceptar | Enter, Z o Espacio | Clic izquierdo |
| Volver / cancelar | Esc o X | Clic derecho |
| Sonido on/off | M | — |

## Pruebas
```bash
python -m unittest discover -s tests -t . -v
```
Las pruebas de la interfaz gráfica no abren ninguna ventana (el juego se dibuja en un framebuffer).

## Contenido del juego
- **Héroes:** Guerrero, Mago, Pícaro (habilidad especial propia).
- **Compañeros (taberna, hasta 2):** Clérigo (cura), Arquero, Caballero (guardia), Alquimista. Suben de nivel contigo.
- **Combate en grupo:** actúa cada miembro en orden; luego ataca el enemigo a uno al azar. Atacar, habilidad, defender, objeto (sobre quien elijas) y huir.
- **Enemigos:** 7 criaturas que aparecen según el piso + 5 jefes (Rey Slime, Señor Goblin, Dragón, Golem, Lich).
- **Tienda:** más de 20 artículos (pociones, éteres, 5 armas, 5 armaduras, 4 accesorios) que se desbloquean por piso; también se puede vender.
- **Posada:** recupera todo el grupo. **Eventos:** cofres, fuentes curativas y trampas.

## Capas
| Capa | Carpeta | Responsable |
|------|---------|-------------|
| Dominio (POO) | `src/domain/` | Célula 1 |
| Servicios y Datos | `src/services/` | Célula 2 |
| Interfaz CLI | `src/ui/cli_interface.py` + `src/main.py` | Célula 3 |
| Interfaz gráfica 8-bit | `src/ui/gui/` | Célula 3 |

Dependencias: `ui → services → domain` (nunca al revés). Ver `architecture.md`.
Para repartir el trabajo y usar Git en equipo: **`GUIA_EQUIPO.md`**.

## Cómo agregar contenido (sin tocar la lógica)
- Nuevo enemigo o jefe: una fila en `src/services/content.py` (+ su sprite en `src/ui/gui/sprites.py`).
- Nuevo artículo de tienda: una `ShopEntry` en `content.py`.
- Nuevo compañero: una clase en `src/domain/models.py` (`Companion`), registrarla en `COMPANION_CLASSES`, una fila en `RECRUITS` y su sprite.

## Flujo de Git
Ramas: `feature/dominio`, `feature/servicios`, `feature/ui`. Nadie hace commit directo en `main`.
Solo el GitMaster hace merge a `main` tras revisar el Pull Request.


