from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Final

from .errors import ByteLangError
from .primitives import PrimitiveCollection, PrimitiveType
from .tools import FileTool, ReprTool


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
        if (datatype := PrimitiveCollection.get(arg.rstrip(PrimitiveType.POINTER_CHAR))) is not None:
            return Argument(datatype, PrimitiveType.POINTER_CHAR == arg[-1])
        raise ByteLangError(f"Error in package '{self.PATH}', Instruction '{name}', at arg: {i} unknown type: '{arg}'")

    def __loadInstructions(self):
        ret = dict[str, Instruction]()
        _id: int = 0

        for line in FileTool.read(self.PATH).split("\n"):
            line = line.split("#")[0].strip()

            if line == "":
                continue

            name, *arg_types = line.split()

            if name in ret.keys():
                raise KeyError(f"In ByteLang Instruction package '{self.PATH}' redefinition of '{name}'")

            ret[name] = Instruction(self.NAME, name, _id, tuple(self.__prepareArgument(arg_t, name) for arg_t in enumerate(arg_types)))
            _id += 1

        return ret


class Platform:
    """Характеристики платформы"""

    def __init__(self, json_path: str):
        self.PATH: Final[str] = json_path
        """путь к конфигурации платформы"""
        self.NAME: Final[str] = pathlib.Path(json_path).stem
        """имя конфигурации"""

        data = FileTool.readJSON(self.PATH)

        self.HEAP_PTR = PrimitiveCollection.pointer(data["ptr_heap"])
        """Указатель кучи"""
        self.PROG_PTR = PrimitiveCollection.pointer(data["ptr_prog"])
        """Указатель в программе"""
        self.INST_PTR = PrimitiveCollection.pointer(data["ptr_inst"])
        """Указатель в таблице инструкций"""
        self.TYPE_PTR = PrimitiveCollection.pointer(data["ptr_type"])
        """Маркер типа переменной из кучи"""
        self.PROGRAM_LEN = data["prog_len"]
        """Максимальный размер программы"""

    def __repr__(self):
        return f"Platform '{self.NAME}' from '{self.PATH}'"


@dataclass(init=True, repr=False, eq=False)
class Argument:
    """Аргумент инструкции"""

    datatype: PrimitiveType
    """Тип данных аргумента"""

    pointer: bool
    """Является указателем"""

    def __repr__(self):
        return f"{self.datatype}{PrimitiveType.POINTER_CHAR * self.pointer}"

    def getPrimitive(self, platform: Platform) -> PrimitiveType:
        return platform.HEAP_PTR if self.pointer else self.datatype


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
        return f"{self.package}::{self.name}@{self.id}{ReprTool.iter(self.signature)}"

    def getSize(self, platform: Platform, inlined: bool) -> int:
        """Размер скомпилированной инструкции в байтах"""

        ret = platform.INST_PTR.size  # Указатель инструкции

        if self.signature:
            ret += sum(arg.getPrimitive(platform).size for arg in self.signature[:-1])  # not-inline аргументы
            argument = self.signature[-1]
            ret += self.signature[-1].datatype.size if inlined else argument.getPrimitive(platform).size  # inline аргумент

        return ret


class PointerVariable:
    def __init__(self, name: str, address: int, _type: PrimitiveType, value: bytes):
        self.name = name
        self.address = address
        self.type = _type
        self.value = value

    def __repr__(self):
        return f"({self.type}) {self.name}@{self.address} = {self.type.read(self.value)}"

    def write(self, platform: Platform) -> bytes:  # TODO кластеры переменных в куче по типам
        """Получить представление в куче"""
        return platform.TYPE_PTR.write(self.type.id) + self.value

    def getSize(self, platform: Platform) -> int:
        """Размер переменной в байтах"""
        return platform.TYPE_PTR.size + self.type.size


@dataclass(frozen=True)
class InstructionUnit:
    instruction: Instruction
    args: tuple[bytes, ...]
    inline_last: bool

    def write(self, platform: Platform) -> bytes:
        """Представление байткода"""
        instruction_ptr_value = int(self.instruction.id)
        sign = list(self.instruction.signature)

        if self.inline_last:
            instruction_ptr_value |= (1 << (platform.INST_PTR.size * 8 - 1))
            sign[-1].pointer = False

        res = platform.INST_PTR.write(instruction_ptr_value)

        res += b''.join(self.args)

        return res
