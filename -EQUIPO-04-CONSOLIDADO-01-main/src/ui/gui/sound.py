"""Efectos de sonido de 8 bits (ondas cuadradas) generados por código.

No usa librerías externas: en Windows suena con `winsound`; en macOS/Linux
intenta `afplay` / `aplay` / `paplay`. Si nada funciona, el juego sigue mudo.
"""
from __future__ import annotations

import io
import os
import struct
import subprocess
import sys
import tempfile
import wave
from typing import Dict, List, Tuple

RATE = 22050

# nombre -> [(frecuencia Hz, milisegundos)]  (0 Hz = silencio)
SFX: Dict[str, List[Tuple[int, int]]] = {
    "move": [(880, 25)],
    "confirm": [(660, 40), (990, 60)],
    "cancel": [(520, 40), (390, 60)],
    "error": [(200, 90), (150, 120)],
    "hit": [(300, 30), (180, 40), (110, 60)],
    "hurt": [(220, 40), (140, 50), (90, 80)],
    "heal": [(520, 50), (660, 50), (784, 50), (1040, 90)],
    "coin": [(988, 45), (1319, 110)],
    "step": [(140, 25)],
    "alert": [(880, 60), (0, 30), (880, 60), (1175, 100)],
    "defeat": [(400, 60), (300, 60), (200, 60), (120, 160)],
    "win": [(523, 90), (659, 90), (784, 90), (0, 30), (784, 60), (1047, 240)],
    "levelup": [(523, 70), (659, 70), (784, 70), (1047, 70), (784, 70), (1047, 70), (1319, 220)],
    "lose": [(392, 140), (330, 140), (262, 140), (196, 320)],
}


def make_wav(notes: List[Tuple[int, int]], volume: float = 0.25) -> bytes:
    """Genera un WAV mono de 16 bits con ondas cuadradas."""
    frames = bytearray()
    amp = int(32767 * volume)
    for freq, ms in notes:
        count = int(RATE * ms / 1000)
        if freq <= 0:
            frames += struct.pack("<h", 0) * count
            continue
        half = max(1, int(RATE / (2 * freq)))
        for i in range(count):
            fade = min(1.0, (count - i) / max(1, count * 0.25))  # apagado suave al final
            level = int(amp * fade)
            frames += struct.pack("<h", level if (i // half) % 2 == 0 else -level)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(bytes(frames))
    return buf.getvalue()


class SoundPlayer:
    def __init__(self) -> None:
        self.enabled = True
        self._wavs: Dict[str, bytes] = {}
        self._files: Dict[str, str] = {}
        self._tmpdir = None

    def _wav(self, name: str) -> bytes:
        if name not in self._wavs:
            self._wavs[name] = make_wav(SFX[name])
        return self._wavs[name]

    def play(self, name: str) -> None:
        if not self.enabled or name not in SFX:
            return
        try:
            if sys.platform.startswith("win"):
                import winsound  # type: ignore
                winsound.PlaySound(self._wav(name), winsound.SND_MEMORY | winsound.SND_ASYNC)
                return
            path = self._file(name)
            for cmd in (("afplay", path), ("aplay", "-q", path), ("paplay", path)):
                try:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except FileNotFoundError:
                    continue
        except Exception:  # el sonido nunca debe romper el juego
            self.enabled = False

    def _file(self, name: str) -> str:
        if name not in self._files:
            if self._tmpdir is None:
                self._tmpdir = tempfile.mkdtemp(prefix="pixelquest_")
            path = os.path.join(self._tmpdir, name + ".wav")
            with open(path, "wb") as fh:
                fh.write(self._wav(name))
            self._files[name] = path
        return self._files[name]
