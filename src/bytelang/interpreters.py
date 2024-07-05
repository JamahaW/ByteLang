"""Виртуальный интерпретатор"""

from __future__ import annotations

from os import PathLike
from typing import Callable
from typing import Optional

from bytelang.content import Environment
from bytelang.content import PrimitiveType
from bytelang.registries import PrimitivesRegistry
from bytelang.tools import FileTool


class Interpreter:
    def __init__(self, env: Environment, instructions: tuple[Callable[[], None], ...]) -> None:
        self.__instructions = instructions

        self.__primitive_instruction_index = env.profile.instruction_index
        self.__primitive_heap_pointer = env.profile.pointer_heap
        self.__primitive_program_pointer = env.profile.pointer_program

        self.__stack = bytearray()
        self.__running = False
        self.__program_pointer = 0
        self.__exit_code = 0

        self.__program: Optional[bytearray] = None

    def stackPushPrimitive(self, primitive: PrimitiveType, value: int | float) -> None:
        """Записать значение примитивного типа в стек"""
        self.__stack.extend((primitive.packer.pack(value)))

    def stackPopPrimitive(self, primitive: PrimitiveType) -> int | float:
        """Получить значение примитивного типа из стека"""
        b = bytearray(self.__stack.pop() for _ in range(primitive.size))
        return primitive.packer.unpack(b)[0]

    def ipVariableStackPop(self, primitive: PrimitiveType) -> None:
        """Записать значение примитивного типа из стека в переменную по IP"""
        self.addressWritePrimitive(self.ipReadHeapPointer(), primitive, self.stackPopPrimitive(primitive))

    def ipStackPush(self, primitive: PrimitiveType) -> None:
        """Отправить в стек значение примитивного типа по IP"""
        self.stackPushPrimitive(primitive, self.ipReadPrimitive(primitive))

    def addressWritePrimitive(self, address: int, primitive: PrimitiveType, value: int | float) -> None:
        """Запись примитивный тип по адресу"""
        primitive.packer.pack_into(self.__program, address, value)

    def addressReadPrimitive(self, address: int, primitive: PrimitiveType) -> int | float:
        """Считать примитивный тип по адресу"""
        return primitive.packer.unpack_from(self.__program, address)[0]

    def ipReadVariable(self, primitive: PrimitiveType) -> int | float:
        return self.addressReadPrimitive(self.ipReadHeapPointer(), primitive)

    def ipReadPrimitive(self, primitive: PrimitiveType) -> int | float:
        """Считать значение примитивного типа по IP"""
        p = self.__program_pointer
        self.__program_pointer += primitive.size
        return self.addressReadPrimitive(p, primitive)

    def ipReadInstructionIndex(self) -> int:
        """Получить индекс инструкции по IP"""
        return self.ipReadPrimitive(self.__primitive_instruction_index)

    def ipReadHeapPointer(self) -> int:
        """Получить указатель на кучу по IP"""
        return self.ipReadPrimitive(self.__primitive_heap_pointer)

    def setExitCode(self, code: int) -> None:
        self.__exit_code = code
        self.__running = False

    def run(self, bytecode_filepath: PathLike | str) -> int:
        self.__program_pointer = 0
        self.__running = True
        self.__stack.clear()
        self.__program = bytearray(FileTool.readBytes(bytecode_filepath))

        self.__program_pointer = self.ipReadHeapPointer()

        while self.__running:
            self.__instructions[self.ipReadInstructionIndex()].__call__()

        return self.__exit_code


class STDInterpreter(Interpreter):

    def __init__(self, env: Environment, primitives: PrimitivesRegistry, instructions: tuple[Callable[[], None], ...]):
        super().__init__(env, instructions)
        self.i8 = primitives.get("i8")
        self.u8 = primitives.get("u8")
        self.i16 = primitives.get("i16")
        self.u16 = primitives.get("u16")
        self.i32 = primitives.get("i32")
        self.u32 = primitives.get("u32")
        self.i64 = primitives.get("i64")
        self.u64 = primitives.get("u64")
        self.f32 = primitives.get("f32")
        self.f64 = primitives.get("f64")


class TestInterpreter(STDInterpreter):

    def __init__(self, env: Environment, primitives: PrimitivesRegistry):
        super().__init__(env, primitives, (
            self.__exit,
            self.__print,
            self.__print8,
            self.__inc,
            self.__write,
            self.__push32,
            self.__pop32,
            self.__pop16,
            self.__pop8,
        ))

    @staticmethod
    def stdoutWrite(value: str) -> None:
        print(value, end="")

    def __exit(self) -> None:
        self.setExitCode(self.ipReadPrimitive(self.u8))

    def IPPrint(self, primitive: PrimitiveType) -> None:
        self.stdoutWrite(f"|> {self.ipReadVariable(primitive)}\n")

    def __print(self) -> None:
        self.IPPrint(self.u32)

    def __print8(self) -> None:
        self.IPPrint(self.u8)

    def __inc(self) -> None:
        address = self.ipReadHeapPointer()
        value = self.addressReadPrimitive(address, self.i16)
        self.addressWritePrimitive(address, self.i16, value + 1)

    def __write(self) -> None:
        self.stdoutWrite(chr(self.ipReadPrimitive(self.u8)))

    def __push32(self) -> None:
        self.ipStackPush(self.u32)

    def __pop32(self) -> None:
        self.ipVariableStackPop(self.u32)

    def __pop16(self) -> None:
        self.ipVariableStackPop(self.u16)

    def __pop8(self) -> None:
        self.ipVariableStackPop(self.u8)
