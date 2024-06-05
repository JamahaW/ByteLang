from typing import Optional, Callable

from ..data import Platform, Argument
from ..primitives import PrimitiveType, PrimitiveCollection


class InstructionVM:

    def __init__(self, func: Callable, arg: Optional[str]):
        self.func = func
        self.args = None if arg is None else Argument.fromStr(arg)


class Interpreter:
    def __init__(self):
        self.ip: int = 0
        self.program: Optional[bytes] = None
        self.platform: Optional[Platform] = None
        self.running: bool = False
        self.stack = list[int]()
        self.program_start: int = 0
        self.arg_addr: int = 0
        self.arg_type: Optional[PrimitiveType] = None

        self.__INSTRUCTIONS: dict[int, InstructionVM] = {
            0: InstructionVM(self.__exit, "i8"),
            1: InstructionVM(self.__push, "i16*"),
            2: InstructionVM(self.__pop, "i16*"),
            3: InstructionVM(self.__add, None),
            4: InstructionVM(self.__mul, None),
            5: InstructionVM(self.__sub, None),
            6: InstructionVM(self.__div, None),
            7: InstructionVM(self.__print, "i16*"),
            8: InstructionVM(self.__input, "i16*"),
        }

    def read(self) -> int:
        if self.arg_addr >= self.program_start:
            return self.arg_type.readFrom(self.program, self.arg_addr)

        t_index = self.platform.TYPE_PTR.readFrom(self.program, self.arg_addr)
        t_type = PrimitiveCollection.PRIMITIVES_ID[t_index]
        return t_type.readFrom(self.program, self.arg_addr + self.platform.TYPE_PTR.size)

    def write(self, value: int) -> None:
        t_index = self.platform.TYPE_PTR.readFrom(self.program, self.arg_addr)
        t_type = PrimitiveCollection.PRIMITIVES_ID[t_index]
        t_type.writeTo(self.program, self.arg_addr + self.platform.TYPE_PTR.size, value)

    def run(self, program: bytes, platform: Platform):
        self.running = True

        self.program = bytearray(program)
        self.platform = platform
        self.stack.clear()

        self.ip = platform.HEAP_PTR.readFrom(self.program, 0)
        self.program_start = int(self.ip)

        while self.running:
            index_raw = platform.INST_PTR.readFrom(self.program, self.ip)
            self.ip += platform.INST_PTR.size

            inlined = (index_raw & platform.INLINE_BIT) != 0
            instruction = self.__INSTRUCTIONS[index_raw & platform.INSTRUCTION_INDEX_MASK]

            if (arg := instruction.args) is not None:
                self.arg_type = arg.getPrimitive(platform, inlined)
                self.arg_addr = self.ip if inlined or not arg.pointer else self.arg_type.readFrom(self.program, self.ip)
                self.ip += self.arg_type.size

            instruction.func()

        print(self.stack)

    def push(self, v: int):
        self.stack.append(v)

    def pop(self) -> int:
        return self.stack.pop()

    def __exit(self):
        self.running = False
        print(f"exit {self.read()}")

    def __push(self):
        self.stack.append(self.read())

    def __pop(self):
        self.write(self.pop())

    def __add(self):
        self.push(self.pop() + self.pop())

    def __mul(self):
        self.push(self.pop() * self.pop())

    def __sub(self):
        b = self.pop()
        a = self.pop()
        self.push(a - b)

    def __div(self):
        b = self.pop()
        a = self.pop()
        self.push(a // b)

    def __print(self):
        print(f"|> {self.read()}")

    def __input(self):
        self.write(int(input("<| ")))
