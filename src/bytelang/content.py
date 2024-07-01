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

# TODO реализовать декоратор для сокращения записи дата класса

@dataclass(frozen=True, kw_only=True, order=False)
class BasicContent:
    """
    Абстрактный контент, загружаемый реестрами
    """

    parent: str
    """Родительский контент"""
    name: str
    """Наименование контента"""


@dataclass(frozen=True, kw_only=True, order=False)
class PrimitiveType(BasicContent):
    """
    Примитивный тип данных
    """

    index: int  # TODO проверить что он вообще нужен, зачем мне вообще динамичный каст?
    """Индекс примитивного типа"""
    size: int
    """Размер примитивного типа"""
    signed: bool
    """Имеет знак"""
    packer: Struct
    """Упаковщик структуры"""

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, kw_only=True, order=False, repr=True)
class Profile(BasicContent):
    """
    Профиль виртуальной машины
    """

    max_program_length: Optional[int]
    """Максимальный размер программы. None, если неограничен"""
    pointer_program: PrimitiveType
    """Тип указателя программы (Определяет максимально возможный адрес инструкции)"""
    pointer_heap: PrimitiveType
    """Тип указателя кучи (Определяет максимально возможный адрес переменной"""
    instruction_index: PrimitiveType
    """Тип индекса инструкции (Определяет максимальное кол-во инструкций в профиле"""
    type_index: PrimitiveType
    """Индекс типа переменной"""  # TODO проверить что он вообще нужен, зачем мне вообще динамичный каст?


@dataclass(frozen=True, kw_only=True, order=False, repr=False)
class InstructionArgument:
    """
    Аргумент инструкции
    """

    primitive: PrimitiveType
    """Примитивный тип аргумента"""
    is_pointer: bool
    """Если указатель - значение переменной будет считано как этот тип"""

    def __repr__(self) -> str:
        return f"{self.primitive.__str__()}{'*' * self.is_pointer}"


@dataclass(frozen=True, kw_only=True, order=False, repr=False)
class BasicInstruction(BasicContent):
    """
    Базовые сведения об инструкции
    """

    arguments: tuple[InstructionArgument, ...]
    """Аргументы базовой инструкции"""

    def __repr__(self) -> str:
        return f"{self.parent}::{self.name}{ReprTool.iter(self.arguments)}"


@dataclass(frozen=True, kw_only=True, order=False)
class EnvironmentInstruction(BasicContent):
    """
    Инструкция окружения
    """

    index: int
    """Индекс этой инструкции"""
    package: str
    """Пакет этой команды"""
    arguments: tuple[InstructionArgument, ...]
    """Аргументы окружения. Если тип был указателем, примитивный тип стал соответствовать типу указателя профиля окружения"""

    def __str__(self) -> str:
        return f"{self.package}::{self.name}@{self.index}{ReprTool.iter(self.arguments)}"


@dataclass(frozen=True, kw_only=True, order=False)
class Package(BasicContent):
    """
    Пакет инструкций
    """

    instructions: tuple[BasicInstruction, ...]
    """Базовые инструкции"""


@dataclass(frozen=True, kw_only=True, order=False)
class Environment(BasicContent):
    """
    Окружение виртуальной машины
    """

    profile: Profile
    """Профиль этого окружения (Настройки Виртуальной машины)"""
    instructions: dict[str, EnvironmentInstruction]
    """Словарь инструкций окружения"""
