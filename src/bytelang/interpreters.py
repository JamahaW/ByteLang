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
        self.__stack.extend((primitive.packer.pack(value)))

    def stackPopPrimitive(self, primitive: PrimitiveType) -> int | float:
        b = bytearray(self.__stack.pop() for _ in range(primitive.size))
        return primitive.packer.unpack(b)[0]

    def addressWritePrimitive(self, address: int, primitive: PrimitiveType, value: int | float) -> None:
        primitive.packer.pack_into(self.__program, address, value)

    def addressReadPrimitive(self, address: int, primitive: PrimitiveType) -> int | float:
        return primitive.packer.unpack_from(self.__program, address)[0]

    def ipReadPrimitive(self, primitive: PrimitiveType) -> int | float:
        p = self.__program_pointer
        self.__program_pointer += primitive.size
        return self.addressReadPrimitive(p, primitive)

    def ipReadInstructionIndex(self) -> int:
        return self.ipReadPrimitive(self.__primitive_instruction_index)

    def ipReadHeapPointer(self) -> int:
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
            self.__ins_exit,
            self.__ins_print,
            self.__ins_print8,
            self.__ins_inc,
            self.__ins_write,
            self.__ins__push32,
            self.__ins__pop32,
            self.__ins__pop16,
            self.__ins__pop8,
        ))

    def __ins_exit(self) -> None:
        self.setExitCode(self.ipReadPrimitive(self.u8))

    def __ins_print(self) -> None:
        address = self.ipReadHeapPointer()
        value = self.addressReadPrimitive(address, self.u32)
        print(f"|> {value}")

    def __ins_print8(self) -> None:
        address = self.ipReadHeapPointer()
        value = self.addressReadPrimitive(address, self.u8)
        print(f"|> {value:02X}")

    def __ins_inc(self) -> None:
        address = self.ipReadHeapPointer()
        value = self.addressReadPrimitive(address, self.i16)
        self.addressWritePrimitive(address, self.i16, value + 1)

    def __ins_write(self) -> None:
        value = self.ipReadPrimitive(self.u8)
        print(chr(value), end="")

    def __ins__push32(self) -> None:
        value = self.ipReadPrimitive(self.u32)
        self.stackPushPrimitive(self.u32, value)

    def __ins__pop32(self) -> None:
        addr = self.ipReadHeapPointer()
        value = self.stackPopPrimitive(self.u32)
        self.addressWritePrimitive(addr, self.u32, value)

    def __ins__pop16(self) -> None:
        addr = self.ipReadHeapPointer()
        value = self.stackPopPrimitive(self.u16)
        self.addressWritePrimitive(addr, self.u16, value)

    def __ins__pop8(self) -> None:
        addr = self.ipReadHeapPointer()
        value = self.stackPopPrimitive(self.u8)
        self.addressWritePrimitive(addr, self.u8, value)
