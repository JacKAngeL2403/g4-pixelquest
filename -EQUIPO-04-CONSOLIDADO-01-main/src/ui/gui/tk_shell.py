"""Ventana de Tkinter: lo único que depende de la pantalla real.

Toma el framebuffer de GameApp, lo convierte en PNG ampliado y lo muestra en
una etiqueta. Reenvía teclado y mouse al juego. Tkinter viene con Python.
"""
from __future__ import annotations

import base64
import time

from src.services.app_service import GameService

from .app import GameApp
from .framebuffer import H, W
from .sound import SoundPlayer

KEYMAP = {
    "Up": "up", "Down": "down", "Left": "left", "Right": "right",
    "Return": "confirm", "KP_Enter": "confirm", "Escape": "cancel", "BackSpace": "backspace",
}
# Teclas alternativas (solo cuando no se está escribiendo texto)
ALT_KEYS = {"w": "up", "s": "down", "a": "left", "d": "right", "z": "confirm",
            "space": "confirm", "x": "cancel"}


def run_gui(service: GameService, scale: int = 0) -> None:
    import tkinter as tk  # import tardío: el resto del juego no lo necesita

    app = GameApp(service)
    sound = SoundPlayer()
    root = tk.Tk()
    root.title("PIXEL QUEST")
    root.resizable(False, False)
    if not scale:
        scale = max(2, min(4, (root.winfo_screenheight() - 140) // H))
    label = tk.Label(root, borderwidth=0, highlightthickness=0, bg="black")
    label.pack()
    root.geometry(f"{W * scale}x{H * scale}")
    state = {"image": None, "last": time.time()}

    def render() -> None:
        png = app.render().png(scale)
        state["image"] = tk.PhotoImage(data=base64.b64encode(png))  # guardar la referencia
        label.configure(image=state["image"])

    def tick() -> None:
        now = time.time()
        dt = min(0.1, now - state["last"])
        state["last"] = now
        if app.update(dt):
            render()
        for name in app.pop_sounds():
            sound.play(name)
        if app.should_quit:
            root.destroy()
            return
        root.after(40, tick)

    def on_key(event) -> None:
        sym = event.keysym
        if sym in KEYMAP:
            app.key(KEYMAP[sym])
        elif app.wants_text:
            if event.char and event.char.isprintable():
                app.key("char", event.char)
        elif sym.lower() in ALT_KEYS:
            app.key(ALT_KEYS[sym.lower()])
        elif event.char and event.char.isprintable():
            app.key("char", event.char)

    def to_game(event):
        return event.x // scale, event.y // scale

    root.bind("<Key>", on_key)
    label.bind("<Button-1>", lambda e: app.click(*to_game(e), 1))
    label.bind("<Button-3>", lambda e: app.click(*to_game(e), 3))
    label.bind("<Motion>", lambda e: app.motion(*to_game(e)))
    root.after(10, tick)
    root.mainloop()
