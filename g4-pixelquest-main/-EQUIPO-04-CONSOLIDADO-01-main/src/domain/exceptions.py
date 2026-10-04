"""Excepciones personalizadas del dominio de Pixel-Quest."""

from typing import Any, Optional


class PixelQuestError(Exception):
    """Excepción base de todo el juego."""

    def __init__(self, message: Optional[str] = None) -> None:
        self.message = (
            message
            if message is not None
            else (self.__doc__.strip() if self.__doc__ else "Error de Pixel-Quest.")
        )
        super().__init__(self.message)


class InvalidNameError(PixelQuestError):
    """El nombre está vacío o supera el largo permitido."""

    def __init__(
        self,
        name: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.name = name
        base_message = self.__doc__.strip() if self.__doc__ else "Nombre inválido."
        if message is None:
            message = (
                f"{base_message} Nombre recibido: {name!r}."
                if name is not None
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class InvalidStatError(PixelQuestError):
    """Una estadística (HP, ataque, valor...) tiene un valor inválido."""

    def __init__(
        self,
        stat_name: Optional[str] = None,
        value: Any = None,
        minimum: Any = None,
        maximum: Any = None,
        message: Optional[str] = None,
    ) -> None:
        self.stat_name = stat_name
        self.value = value
        self.minimum = minimum
        self.maximum = maximum
        base_message = self.__doc__.strip() if self.__doc__ else "Estadística inválida."
        if message is None:
            details = []
            if stat_name is not None:
                details.append(f"Estadística: {stat_name!r}")
            if value is not None:
                details.append(f"Valor: {value!r}")
            if minimum is not None or maximum is not None:
                expected = (
                    f"{minimum!r}..{maximum!r}"
                    if minimum is not None and maximum is not None
                    else f">= {minimum!r}" if minimum is not None else f"<= {maximum!r}"
                )
                details.append(f"Rango esperado: {expected}")
            message = (
                f"{base_message} {'; '.join(details)}."
                if details
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class InventoryFullError(PixelQuestError):
    """El inventario alcanzó su capacidad máxima."""

    def __init__(
        self,
        capacity: Optional[int] = None,
        current_count: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        self.capacity = capacity
        self.current_count = current_count
        base_message = self.__doc__.strip() if self.__doc__ else "Inventario lleno."
        if message is None:
            details = []
            if capacity is not None:
                details.append(f"Capacidad: {capacity}")
            if current_count is not None:
                details.append(f"Cantidad actual: {current_count}")
            message = (
                f"{base_message} {'; '.join(details)}."
                if details
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class ItemNotFoundError(PixelQuestError):
    """No existe un objeto en la posición indicada."""

    def __init__(
        self,
        item_name: Optional[str] = None,
        item_index: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        self.item_name = item_name
        self.item_index = item_index
        base_message = self.__doc__.strip() if self.__doc__ else "Ítem no encontrado."
        if message is None:
            details = []
            if item_index is not None:
                details.append(f"Índice: {item_index}")
            if item_name is not None:
                details.append(f"Nombre: {item_name!r}")
            message = (
                f"{base_message} {'; '.join(details)}."
                if details
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class InvalidItemError(PixelQuestError):
    """El objeto no se puede usar/equipar de esa forma."""

    def __init__(
        self,
        item_name: Optional[str] = None,
        action: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.item_name = item_name
        self.action = action
        base_message = self.__doc__.strip() if self.__doc__ else "Ítem inválido."
        if message is None:
            details = []
            if item_name is not None:
                details.append(f"Ítem: {item_name!r}")
            if action is not None:
                details.append(f"Acción: {action}")
            message = (
                f"{base_message} {'; '.join(details)}."
                if details
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class NotEnoughGoldError(PixelQuestError):
    """El héroe no tiene oro suficiente."""

    def __init__(
        self,
        gold_available: Optional[int] = None,
        gold_required: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        self.gold_available = gold_available
        self.gold_required = gold_required
        self.missing_gold = (
            max(gold_required - gold_available, 0)
            if gold_required is not None and gold_available is not None
            else None
        )
        base_message = self.__doc__.strip() if self.__doc__ else "No hay suficiente oro."
        if message is None:
            details = []
            if gold_available is not None:
                details.append(f"Oro disponible: {gold_available}")
            if gold_required is not None:
                details.append(f"Oro requerido: {gold_required}")
            if self.missing_gold is not None:
                details.append(f"Oro faltante: {self.missing_gold}")
            message = (
                f"{base_message} {'; '.join(details)}."
                if details
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class CombatError(PixelQuestError):
    """Acción de combate no permitida."""

    def __init__(
        self,
        attacker: Optional[str] = None,
        defender: Optional[str] = None,
        action: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.attacker = attacker
        self.defender = defender
        self.action = action
        base_message = self.__doc__.strip() if self.__doc__ else "Error de combate."
        if message is None:
            details = []
            if attacker is not None:
                details.append(f"Atacante: {attacker!r}")
            if defender is not None:
                details.append(f"Defensor: {defender!r}")
            if action is not None:
                details.append(f"Acción: {action}")
            message = (
                f"{base_message} {'; '.join(details)}."
                if details
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class HeroNotFoundError(PixelQuestError):
    """No existe un héroe guardado con ese nombre."""

    def __init__(
        self,
        hero_name: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.hero_name = hero_name
        base_message = self.__doc__.strip() if self.__doc__ else "Héroe no encontrado."
        if message is None:
            message = (
                f"{base_message} Nombre recibido: {hero_name!r}."
                if hero_name is not None
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class DuplicateHeroError(PixelQuestError):
    """Ya existe un héroe con ese nombre."""

    def __init__(
        self,
        hero_name: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.hero_name = hero_name
        base_message = self.__doc__.strip() if self.__doc__ else "Héroe duplicado."
        if message is None:
            message = (
                f"{base_message} Nombre recibido: {hero_name!r}."
                if hero_name is not None
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class SaveDataError(PixelQuestError):
    """El archivo de guardado está dañado o no se pudo leer/escribir."""

    def __init__(
        self,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.file_path = file_path
        self.operation = operation
        base_message = self.__doc__.strip() if self.__doc__ else "Error al guardar/cargar datos."
        if message is None:
            details = []
            if file_path is not None:
                details.append(f"Archivo: {file_path!r}")
            if operation is not None:
                details.append(f"Operación: {operation}")
            message = (
                f"{base_message} {'; '.join(details)}."
                if details
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class PartyError(PixelQuestError):
    """Operación de grupo no válida (compañero repetido, índice inexistente...)."""

    def __init__(
        self,
        member_name: Optional[str] = None,
        index: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        self.member_name = member_name
        self.index = index
        base_message = self.__doc__.strip() if self.__doc__ else "Error de grupo."
        if message is None:
            details = []
            if member_name is not None:
                details.append(f"Miembro: {member_name!r}")
            if index is not None:
                details.append(f"Índice: {index}")
            message = (
                f"{base_message} {'; '.join(details)}."
                if details
                else base_message
            )
        self.message = message
        super().__init__(self.message)


class PartyFullError(PartyError):
    """El grupo ya tiene el máximo de compañeros."""

    def __init__(
        self,
        current_size: Optional[int] = None,
        max_party_size: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        self.current_size = current_size
        self.max_party_size = max_party_size
        base_message = self.__doc__.strip() if self.__doc__ else "El grupo está lleno."
        if message is None:
            details = []
            if current_size is not None:
                details.append(f"Tamaño actual: {current_size}")
            if max_party_size is not None:
                details.append(f"Tamaño máximo: {max_party_size}")
            message = (
                f"{base_message} {'; '.join(details)}."
                if details
                else base_message
            )
        self.message = message
        super().__init__(message=self.message)