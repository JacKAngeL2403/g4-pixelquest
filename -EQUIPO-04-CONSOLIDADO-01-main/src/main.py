"""Punto de entrada. Ejecutar desde la raíz del proyecto:

    python -m src.main            -> interfaz gráfica 8-bit (por defecto)
    python -m src.main --cli      -> versión de consola
    python -m src.main --scale 3  -> tamaño de la ventana (2, 3 o 4)
"""
import argparse
import sys
from pathlib import Path

# Permite también ejecutar `python src/main.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.app_service import GameService  # noqa: E402
from src.services.data_manager import DataManager  # noqa: E402
from src.ui.cli_interface import MenuCLI  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Pixel-Quest - RPG de mazmorras")
    parser.add_argument("--cli", action="store_true", help="usar la versión de consola")
    parser.add_argument("--scale", type=int, default=0, help="ampliación de la ventana (2-4)")
    args = parser.parse_args()

    service = GameService(DataManager("data/heroes.json"))
    if args.cli:
        MenuCLI(service).run()
        return
    try:
        from src.ui.gui.tk_shell import run_gui
        import tkinter  # noqa: F401
    except ImportError:
        print("No se encontró Tkinter (la interfaz gráfica). Usando la versión de consola.")
        print("En Linux instálalo con: sudo apt install python3-tk")
        MenuCLI(service).run()
        return
    run_gui(service, args.scale)


if __name__ == "__main__":
    main()
