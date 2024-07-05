"""Виртуальный интерпретатор"""

from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from typing import Callable
from typing import Optional

from bytelang.content import Environment
from bytelang.content import PrimitiveType
from bytelang.registries import PrimitiveTypeRegistry


@dataclass(frozen=True)
class InterpreterInstruction:
    """Инструкция интерпретатора"""

    debug_name: str
    """Имя для отладки"""
    handler: Callable[[], None]
    """Обработчик"""


class Interpreter:
    def __init__(self, env: Environment, bytecode_filepath: PathLike | str, primitives: PrimitiveTypeRegistry) -> None:
        with open(bytecode_filepath, "rb") as f:
            self.__program = bytearray(f.read())

        self.__primitive_instruction_index = env.profile.instruction_index
        self.__primitive_heap_pointer = env.profile.pointer_heap
        self.__primitive_program_pointer = env.profile.pointer_program

        self.__program_pointer: int = 0

        self.__u8 = primitives.get("u8")
        self.__i16 = primitives.get("i16")

        self.__instructions: tuple[InterpreterInstruction, ...] = (
            InterpreterInstruction("exit", self.__ins_exit),
            InterpreterInstruction("print", self.__ins_print),
            InterpreterInstruction("inc", self.__ins_inc),
            InterpreterInstruction("write", self.__ins_write),
        )

        self.__running = False
        self.__exit_code: Optional[int] = None

    def __ins_exit(self) -> None:
        self.__exit_code = self.__readIPPrimitiveInteger(self.__u8)
        self.__running = False

    def __ins_print(self) -> None:
        address = self.__readIPHeapPointer()
        value = self.__readAddressPrimitiveInteger(address, self.__i16)
        print(f"|> {value}")

    def __ins_inc(self) -> None:
        address = self.__readIPHeapPointer()
        value = self.__readAddressPrimitiveInteger(address, self.__i16)
        self.__writeAddressPrimitiveInteger(address, self.__i16, value + 1)

    def __ins_write(self) -> None:
        value = self.__readIPPrimitiveInteger(self.__u8)
        print(chr(value), end="")

    def __writeAddressPrimitiveInteger(self, address: int, primitive: PrimitiveType, value: int) -> None:
        primitive.packer.pack_into(self.__program, address, value)

    def __readAddressPrimitiveInteger(self, address: int, primitive: PrimitiveType) -> int:
        return primitive.packer.unpack_from(self.__program, address)[0]

    def __readIPPrimitiveInteger(self, primitive: PrimitiveType) -> int:
        p = self.__program_pointer
        self.__program_pointer += primitive.size
        return self.__readAddressPrimitiveInteger(p, primitive)

    def __readIPInstructionIndex(self) -> int:
        return self.__readIPPrimitiveInteger(self.__primitive_instruction_index)

    def __readIPHeapPointer(self) -> int:
        return self.__readIPPrimitiveInteger(self.__primitive_heap_pointer)

    def run(self) -> int:
        self.__program_pointer = self.__readIPHeapPointer()
        self.__running = True

        while self.__running:
            self.__instructions[self.__readIPInstructionIndex()].handler()

        return self.__exit_code
