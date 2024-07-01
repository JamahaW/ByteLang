"""
Контент, который можно получить из реестров
"""

from __future__ import annotations

from dataclasses import dataclass
from struct import Struct
from typing import Optional

from bytelang.tools import ReprTool


# TODO реализовать реестры
#  инструкций окружения
#  переменных
#  констант
#  Примитивных типов
#  Аргументов

# TODO реализовать декоратор для сокращения записи дата класса

@dataclass(frozen=True, kw_only=True, order=False, repr=False)
class BasicContent:
    """
    Абстрактный контент, загружаемый реестрами
    """

    parent: str
    name: str

    def __repr__(self) -> str:
        return f"{self.parent}::{self.name}"


@dataclass(frozen=True, kw_only=True, order=False, repr=False)
class PrimitiveType(BasicContent):
    """
    Примитивный тип данных
    """

    index: int
    size: int
    signed: bool
    packer: Struct

    def __repr__(self) -> str:
        return f"PrimitiveType {self.signed=}({self.size}) {self.parent}::{self.name}@{self.index}"

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, kw_only=True, order=False, repr=True)
class Profile(BasicContent):
    """
    Профиль виртуальной машины
    """

    max_program_length: Optional[int]
    pointer_program: PrimitiveType
    pointer_heap: PrimitiveType
    instruction_index: PrimitiveType
    type_index: PrimitiveType


@dataclass(frozen=True, kw_only=True, order=False, repr=False)
class InstructionArgument:
    """
    Аргумент инструкции
    """

    primitive: PrimitiveType
    is_pointer: bool

    def __repr__(self) -> str:
        return f"{self.primitive.__str__()}{'*' * self.is_pointer}"


@dataclass(frozen=True, kw_only=True, order=False, repr=False)
class BasicInstruction(BasicContent):
    """
    Базовые сведения об инструкции
    """

    arguments: tuple[InstructionArgument, ...]

    def __repr__(self) -> str:
        return f"{self.parent}::{self.name}{ReprTool.iter(self.arguments)}"


@dataclass(frozen=True, kw_only=True, order=False)
class Package(BasicContent):
    """
    Пакет инструкций
    """

    instructions: tuple[BasicInstruction, ...]


@dataclass(frozen=True, kw_only=True, order=False)
class Environment(BasicContent):
    """
    Окружение виртуальной машины
    """

    profile: Profile
    #  TODO "продвинутые" инструкции, с индексом и всем под это окружение
    instructions: tuple[object, ...]
