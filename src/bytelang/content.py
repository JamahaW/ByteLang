"""
Контент, который можно получить из реестров
"""
from dataclasses import dataclass
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


@dataclass(frozen=True, kw_only=True, order=False)
class Profile(BasicContent):
    """
    Профиль виртуальной машины
    """

    max_program_length: Optional[int]
    pointer_program: object
    pointer_heap: object
    instruction_index: object
    type_index: object


@dataclass(frozen=True, kw_only=True, order=False)
class InstructionArgument:
    """
    Аргумент инструкции
    """

    datatype: object  # TODO примитивный тип
    is_pointer: bool


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
