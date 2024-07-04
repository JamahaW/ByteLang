"""
Контент, который можно получить из реестров
"""
# TODO найти подходящее название

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from enum import auto
from struct import Struct
from typing import ClassVar
from typing import Final
from typing import Optional

from bytelang.tools import ReprTool


@dataclass(frozen=True, kw_only=True)
class Content:
    """Абстрактный контент, загружаемый реестрами"""

    parent: str
    """Родительский контент"""
    name: str
    """Наименование контента"""


class PrimitiveWriteType(Enum):
    """Способ записи данных примитивного типа"""

    signed = auto()
    unsigned = auto()
    exponent = auto()

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, kw_only=True)
class PrimitiveType(Content):
    """Примитивный тип данных"""

    INTEGER_FORMATS: ClassVar[dict[int, str]] = {
        1: "B",
        2: "H",
        4: "I",
        8: "Q"
    }

    EXPONENT_FORMATS: ClassVar[dict[int, str]] = {
        4: "f",
        8: "d"
    }

    index: int
    """Индекс примитивного типа"""
    size: int
    """Размер примитивного типа"""
    write_type: PrimitiveWriteType
    """Способ записи"""
    packer: Struct
    """Упаковщик структуры"""

    def __repr__(self) -> str:
        return f"[{self.write_type} {self.size * 8}-bit] {self.__str__()}@{self.index}"

    def __str__(self) -> str:
        return f"{self.parent}::{self.name}"


@dataclass(frozen=True, kw_only=True)
class Profile(Content):
    """Профиль виртуальной машины"""

    max_program_length: Optional[int]
    """Максимальный размер программы. None, если неограничен"""
    pointer_program: PrimitiveType
    """Тип указателя программы (Определяет максимально возможный адрес инструкции)"""
    pointer_heap: PrimitiveType
    """Тип указателя кучи (Определяет максимально возможный адрес переменной"""
    instruction_index: PrimitiveType
    """Тип индекса инструкции (Определяет максимальное кол-во инструкций в профиле"""
    type_index: PrimitiveType
    """Индекс типа переменной"""


@dataclass(frozen=True, kw_only=True)
class InstructionArgument:
    """Аргумент инструкции"""

    POINTER_CHAR: Final[ClassVar[str]] = "*"

    primitive: PrimitiveType
    """Примитивный тип аргумента"""
    is_pointer: bool
    """Если указатель - значение переменной будет считано как этот тип"""

    def __repr__(self) -> str:
        return f"{self.primitive.__str__()}{self.POINTER_CHAR * self.is_pointer}"

    def transform(self, profile: Profile) -> InstructionArgument:
        """Получить аргумент с актуальным примитивным типом на основе профиля."""
        if not self.is_pointer:
            return self

        return InstructionArgument(primitive=profile.pointer_heap, is_pointer=self.is_pointer)


@dataclass(frozen=True, kw_only=True)
class PackageInstruction(Content):
    """Базовые сведения об инструкции"""

    arguments: tuple[InstructionArgument, ...]
    """Аргументы базовой инструкции"""

    def __repr__(self) -> str:
        return f"{self.parent}::{self.name}{ReprTool.iter(self.arguments)}"

    def transform(self, index: int, profile: Profile) -> EnvironmentInstruction:
        """Создать инструкцию окружения на основе базовой и профиля"""
        args = tuple(arg.transform(profile) for arg in self.arguments)
        size = profile.instruction_index.size + sum(arg.primitive.size for arg in args)
        return EnvironmentInstruction(
            parent=profile.name,
            name=self.name,
            index=index,
            package=self.parent,
            arguments=args,
            size=size
        )


@dataclass(frozen=True, kw_only=True)
class EnvironmentInstruction(Content):
    """Инструкция окружения"""

    index: int
    """Индекс этой инструкции"""
    package: str
    """Пакет этой команды"""
    arguments: tuple[InstructionArgument, ...]
    """Аргументы окружения. Если тип был указателем, примитивный тип стал соответствовать типу указателя профиля окружения"""
    size: int
    """Размер инструкции в байтах"""

    def generalInfo(self) -> str:
        return f"[{self.size}B] {self.package}::{self.name}@{self.index}"

    def __repr__(self) -> str:
        return f"{self.generalInfo()}{ReprTool.iter(self.arguments)}"


@dataclass(frozen=True, kw_only=True)
class Package(Content):
    """Пакет инструкций"""

    instructions: tuple[PackageInstruction, ...]
    """Набор инструкций"""


@dataclass(frozen=True, kw_only=True)
class Environment(Content):
    """Окружение виртуальной машины"""

    profile: Profile
    """Профиль этого окружения (Настройки Виртуальной машины)"""
    instructions: dict[str, EnvironmentInstruction]
    """Инструкции окружения"""
