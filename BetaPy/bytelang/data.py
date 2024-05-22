from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Final

from .errors import ByteLangError
from .primitives import PrimitiveCollection, PrimitiveType
from .utils import File


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
        return {
            name: Instruction(self.NAME, name, index, tuple(self.__prepareArgument(i_arg, name) for i_arg in enumerate(signature)))
            for index, (name, signature) in enumerate(File.readPackage(self.PATH))
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

        data: Final[Platform.__Params] = Platform.__Params(**File.readJSON(self.PATH))

        self.HEAP_PTR = PrimitiveCollection.pointer(data.ptr_heap)
        """Указатель кучи"""
        self.PROG_PTR = PrimitiveCollection.pointer(data.ptr_prog)
        """Указатель в программе"""
        self.INST_PTR = PrimitiveCollection.pointer(data.ptr_inst)
        """Указатель в таблице инструкций"""
        self.TYPE_PTR = PrimitiveCollection.pointer(data.ptr_type)
        """Маркер типа переменной из кучи"""
        self.PROGRAM_LEN = data.prog_len
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
        return self.datatype.__str__() + PrimitiveType.POINTER_CHAR if self.pointer else ''

    def getSize(self, platform: Platform) -> int:
        return (platform.HEAP_PTR if self.pointer else self.datatype).size

    def toBytes(self, platform: Platform, value: int) -> bytes:
        return (platform.HEAP_PTR if self.pointer else self.datatype).toBytes(value)


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

        ret = platform.INST_PTR.size  # Указатель инструкции
        ret += sum(arg.getSize(platform) for arg in self.signature[:-1])  # not-inline аргументы
        ret += self.signature[-1].datatype.size if inlined else self.signature[-1].getSize(platform)  # inline аргумент

        return ret


class PointerVariable:
    def __init__(self, name: str, heap_ptr: int, _type: PrimitiveType, value: bytes):
        self.name = name
        self.ptr = heap_ptr
        self.type = _type
        self.value = value

    def __repr__(self):
        return f"({self.type}) {self.name}@{self.ptr} = {self.value.hex()}"

    def toBytes(self, platform: Platform) -> bytes:  # TODO кластеры переменных в куче по типам
        """Получить представление в куче"""
        return platform.TYPE_PTR.toBytes(self.type.id) + self.value

    def getSize(self, platform: Platform) -> int:
        """Размер переменной в байтах"""
        return platform.TYPE_PTR.size + self.type.size


@dataclass(frozen=True)
class InstructionUnit:
    instruction: Instruction
    args: tuple[bytes, ...]
    inline_last: bool

    def toBytes(self, platform: Platform) -> bytes:
        """Представление байткода"""
        instruction_ptr_value = int(self.instruction.id)
        sign = list(self.instruction.signature)

        if self.inline_last:
            instruction_ptr_value |= (1 << (platform.INST_PTR.size * 8 - 1))
            sign[-1].pointer = False

        res = platform.INST_PTR.toBytes(instruction_ptr_value)

        for arg_v in self.args:
            res += arg_v

        return res
