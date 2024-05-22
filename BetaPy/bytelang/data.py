from __future__ import annotations

import enum
import pathlib
from dataclasses import dataclass
from typing import Final

from . import utils, primitives
from .errors import ByteLangError


class Package:
    """Пакет инструкций"""

    def __init__(self, package_path: str):
        self.PATH: str = package_path
        """Путь к пакету"""
        self.NAME: str = pathlib.Path(package_path).stem
        """Уникальный идентификатор пакета"""
        self.INSTRUCTIONS: Final[dict[str, Instruction]] = self.__loadInstructions()
        """Набор инструкций"""

    def __repr__(self):
        return f"Package '{self.NAME}' from '{self.PATH}' instructions: {self.INSTRUCTIONS}"

    def __prepareArgument(self, i_arg, name) -> Argument:
        i, arg = i_arg
        if (datatype := primitives.Collection.get(arg.rstrip(primitives.Type.POINTER_CHAR))) is not None:
            return Argument(datatype, primitives.Type.POINTER_CHAR == arg[-1])
        raise ByteLangError(f"Error in package '{self.PATH}', Instruction '{name}', at arg: {i} unknown type: '{arg}'")

    def __loadInstructions(self):
        return {
            name: Instruction(self.NAME, name, index, tuple(self.__prepareArgument(i_arg, name) for i_arg in enumerate(signature)))
            for index, (name, signature) in enumerate(utils.File.readPackage(self.PATH))
        }


class Platform:
    """Характеристики платформы"""

    @dataclass(frozen=True, kw_only=True, eq=False, order=False)
    class __Params:
        info: str
        prog_len: int
        ptr_prog: int
        ptr_heap: int
        ptr_inst: int
        ptr_type: int

    def __init__(self, json_path: str):
        self.PATH: Final[str] = json_path
        """путь к конфигурации платформы"""
        self.NAME: Final[str] = pathlib.Path(json_path).stem
        """имя конфигурации"""
        self.DATA: Final[Platform.__Params] = Platform.__Params(**utils.File.readJSON(self.PATH))
        """Параметры платформы"""
        self.HEAP_PTR = primitives.Collection.pointer(self.DATA.ptr_heap)
        """Указатель кучи"""
        self.PROG_PTR = primitives.Collection.pointer(self.DATA.ptr_prog)
        """Указатель в программе"""
        self.INST_PTR = primitives.Collection.pointer(self.DATA.ptr_inst)
        """Указатель в таблице инструкций"""
        self.TYPE_PTR = primitives.Collection.pointer(self.DATA.ptr_type)
        """Маркер типа переменной из кучи"""

    def __repr__(self):
        return f"Platform '{self.NAME}' from '{self.PATH}' data={self.DATA}"


class ContextLoader:
    """Менеджер загрузки контекста"""

    def __init__(self, T):
        self.T = T
        self.__loaded = dict[str, T]()
        self.used: T | None = None

    def load(self, path: str):
        _l = self.T(path)
        self.__loaded[_l.NAME] = _l

    def use(self, name: str):
        if (used := self.__loaded.get(name)) is None:
            raise ByteLangError(f"unknown {self.T} identifier: {name}")
        self.used = used


class StatementType(enum.Enum):
    DIRECTIVE = enum.auto()
    MARK = enum.auto()
    INSTRUCTION = enum.auto()


@dataclass(frozen=True, eq=False)
class Statement:
    """Выражение"""

    type: StatementType
    lexeme: str
    args: tuple[str, ...]
    line: int


@dataclass(init=True, repr=False, eq=False)
class Argument:
    """Аргумент инструкции"""

    datatype: primitives.Type
    """Тип данных аргумента"""

    pointer: bool
    """Является указателем"""

    def __repr__(self):
        return self.datatype.__str__() + primitives.Type.POINTER_CHAR if self.pointer else ''

    def getSize(self, platform: Platform) -> int:
        return platform.DATA.ptr_heap if self.pointer else self.datatype.size


class Instruction:
    """Инструкция"""

    def __init__(self, package: str, name: str, _id: int, signature: tuple[Argument, ...]):
        self.signature: Final[tuple[Argument, ...]] = signature
        """Сигнатура"""

        self.name: Final[str] = name
        """Уникальный строчный идентификатор инструкции"""

        self.id: Final[int] = _id
        """Уникальный индекс инструкции"""

        self.can_inline: Final[bool] = len(signature) > 0 and signature[-1].pointer == True
        """Может ли последний аргумент инструкции быть поставлен по значению?"""

        self.package = package

    def __repr__(self):
        return f"{self.package}::{self.name}@{self.id}{self.signature}"

    def getSize(self, platform: Platform, inlined: bool) -> int:
        """Размер скомпилированной инструкции в байтах"""

        ret = platform.DATA.ptr_inst  # Указатель инструкции
        ret += sum(arg.getSize(platform) for arg in self.signature[:-1])  # not-inline аргументы
        ret += self.signature[-1].datatype.size * inlined  # inline аргумент

        return ret
