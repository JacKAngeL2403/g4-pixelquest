"""Capa 2 - Persistencia: guarda y lee héroes en un archivo JSON."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.domain.exceptions import HeroNotFoundError, SaveDataError


class DataManager:
    """Maneja el archivo JSON. Solo trabaja con diccionarios (no conoce Hero)."""

    def __init__(self, filepath: str = "data/heroes.json") -> None:
        self._path = Path(filepath)

    @staticmethod
    def _key(name: str) -> str:
        return name.strip().lower()

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        if not self._path.exists():
            return {}
        try:
            with self._path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            raise SaveDataError(f"No se pudo leer el guardado: {exc}") from exc
        if not isinstance(data, dict):
            raise SaveDataError("El archivo de guardado tiene un formato inválido.")
        return data

    def save_all(self, data: Dict[str, Dict[str, Any]]) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            tmp.replace(self._path)  # escritura atómica
        except OSError as exc:
            raise SaveDataError(f"No se pudo guardar: {exc}") from exc

    def exists(self, name: str) -> bool:
        return self._key(name) in self.load_all()

    def save_hero(self, name: str, hero_data: Dict[str, Any]) -> None:
        data = self.load_all()
        data[self._key(name)] = hero_data
        self.save_all(data)

    def get_hero(self, name: str) -> Dict[str, Any]:
        data = self.load_all()
        try:
            return data[self._key(name)]
        except KeyError as exc:
            raise HeroNotFoundError(f"No existe el héroe '{name}'.") from exc

    def delete_hero(self, name: str) -> None:
        data = self.load_all()
        if self._key(name) not in data:
            raise HeroNotFoundError(f"No existe el héroe '{name}'.")
        del data[self._key(name)]
        self.save_all(data)

    def list_names(self) -> List[str]:
        return [h.get("name", k) for k, h in self.load_all().items()]
