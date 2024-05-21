import typing
from dataclasses import dataclass
from typing import Iterable

from . import utils
from .data import Package, Platform, ContextLoader, StatementType, Statement, Instruction
from .errors import ByteLangError


@dataclass(frozen=True)
class DirectiveUnit:
    name: str
    args: int | None


@dataclass(frozen=True, kw_only=True)
class DirectiveSettings:
    SET_HEAP: DirectiveUnit
    SET_POINTER: DirectiveUnit
    INIT_POINTER: DirectiveUnit
    USE_INLINE: DirectiveUnit
    DEFINE_MACRO: DirectiveUnit


@dataclass(frozen=True)
class CharSettings:
    COMMENT: str
    MARK: str
    DIRECTIVE: str


class PointerVariable:
    def __init__(self, name: str, heap_ptr: int, _type: str):
        self.name = name
        self.ptr = heap_ptr
        self.type = _type
        self.value = 0
        self.has_static_set = False

    def set(self, value: int):
        self.value = value
        self.has_static_set = True

    def __repr__(self):
        return f"({self.type}) {self.name}@{self.ptr} = {self.value}"

    def pack(self, platform: Platform) -> bytes:  # TODO кластеры переменных в куче по типам
        """Получить представление в куче"""
        return utils.BytesLegacy.pack(f"{utils.BytesLegacy.int(platform.DATA.ptr_type)} {self.type}", (utils.BytesLegacy.typeID(self.type), self.value))

    def size(self, platform: Platform) -> int:
        """Размер переменной в байтах"""
        return platform.DATA.ptr_type + utils.BytesLegacy.size(self.type)


@dataclass(init=False)
class ProgramData:
    heap_size: int = 0
    constants = dict[str, int | str]()
    variables = dict[str, PointerVariable]()


class Environment:

    def __init__(self):
        self.packages = ContextLoader(Package)
        self.platforms = ContextLoader(Platform)

        self.CHAR = CharSettings('#', ':', '.')

        self.DIRECTIVE = DirectiveSettings(
            SET_HEAP=DirectiveUnit("heap", 1),
            INIT_POINTER=DirectiveUnit("ptr", 2),
            SET_POINTER=DirectiveUnit("set", 2),
            USE_INLINE=DirectiveUnit("inline", None),
            DEFINE_MACRO=DirectiveUnit("def", 2)
        )

        self.program = ProgramData()

    def getPlatform(self) -> Platform:
        return self.platforms.used

    def getPackage(self) -> Package:
        return self.packages.used

    def statementError(self, message: str, statement: Statement) -> None:
        raise ByteLangError(f"[ ByteLangError ] :: {message} : {statement}")


class Tokeniser:

    def __init__(self, environment: Environment):
        self.environment = environment

    def run(self, source: str) -> Iterable[Statement]:
        ret = list()

        for index, source_line in enumerate(source.split("\n")):
            if (line_no_comment := source_line.split(self.environment.CHAR.COMMENT)[0].strip()) != "":
                ret.append(self.__createStatement(index, line_no_comment, source_line))

        return ret

    def __createStatement(self, index: int, line_clean: str, source_line: str):
        lexeme, *args = line_clean.split()
        _type = None

        if lexeme[-1] == self.environment.CHAR.MARK:
            _type = StatementType.MARK
            lexeme = lexeme[:-1]

        elif lexeme[0] == self.environment.CHAR.DIRECTIVE:
            lexeme = lexeme[1:]
            _type = StatementType.DIRECTIVE

        elif lexeme in self.environment.getPackage().INSTRUCTIONS.keys():
            _type = StatementType.INSTRUCTION
            instruction = self.environment.getPackage().INSTRUCTIONS.get(lexeme)

            if (L := len(args)) != len(instruction.signature):
                raise ByteLangError(f"Invalid arg count for {instruction} got {source_line} ({L})")

        else:
            raise ByteLangError(f"Invalid Statement: '{lexeme}' at Line {index} '{source_line}'")

        return Statement(_type, lexeme, args, index + 1)


@dataclass(frozen=True)
class StatementUnit:
    instruction: Instruction
    args: tuple[int, ...]
    inline_last: bool

    def pack(self, platform: Platform) -> bytes:
        """Представление байткода"""
        ptr_inst_bits = platform.DATA.ptr_inst * 8
        instruction_ptr_value = int(self.instruction.index)
        sign = list(self.instruction.signature)

        if self.inline_last:
            instruction_ptr_value |= (1 << (ptr_inst_bits - 1))
            sign[-1].pointer = True

        heap_p = utils.BytesLegacy.int(platform.DATA.ptr_heap)

        arg_fmt = " ".join(map(lambda x: heap_p if x.pointer else x.type, sign))

        return utils.BytesLegacy.pack(
            f"{utils.BytesLegacy.int(platform.DATA.ptr_inst)} {arg_fmt}",
            (instruction_ptr_value,) + self.args
        )


class Parser:
    BASES_PREF: dict[str, int] = {
        'x': 16,
        'o': 8,
        'b': 2
    }

    def __init__(self, environment: Environment):
        self.environment = environment

        self.MAX_HEAP_SIZE = 2 ** (self.environment.getPlatform().DATA.ptr_heap * 8) - 1

        self.mark_offset: int = 0
        self.ptr_addr_next: int = 0

        self.heap_directive_used = False

        d = self.environment.DIRECTIVE

        self.DIRECTIVES: dict[str, DirectiveUnit] = {
            directive.name: directive for directive in self.environment.DIRECTIVE.__dict__.values()
        }

        self.DIRECTIVE_CALLBACKS: dict[DirectiveUnit, typing.Callable[[Statement], None | StatementUnit]] = {
            d.SET_HEAP: self.directiveSetHeap,
            d.DEFINE_MACRO: self.directiveDefineMacro,
            d.INIT_POINTER: self.directiveInitPointer,
            d.SET_POINTER: self.directiveSetPointer,
            d.USE_INLINE: self.directiveUseInline,
        }

    def run(self, statements: Iterable[Statement]) -> Iterable[StatementUnit]:
        self.mark_offset += self.environment.getPlatform().DATA.ptr_heap
        self.ptr_addr_next = int(self.mark_offset)

        ret = list[StatementUnit]()

        for statement in statements:
            match statement.type:
                case StatementType.MARK:
                    self.environment.program.constants[statement.lexeme] = self.mark_offset

                case StatementType.DIRECTIVE:
                    if (u := self.directive(statement)) is not None:
                        ret.append(u)

                case StatementType.INSTRUCTION:
                    ret.append(self.instruction(statement))

        return ret

    def getValue(self, arg_lexeme: str) -> int:
        """Получить значение из лексемы"""

        # данное значение найдено среди констант
        if (val := self.environment.program.constants.get(arg_lexeme)) is not None:
            return self.getValue(val)

        # если указатель - возвращаем адрес
        if (val := self.environment.program.variables.get(arg_lexeme)) is not None:
            return val.ptr

        # ничего не было найдено, возможно это число

        base = 10

        if len(arg_lexeme) > 2 and arg_lexeme[0] == '0' and (base := self.BASES_PREF.get(arg_lexeme[1])) is None:
            raise ByteLangError(f"IncorrectBasePrefix: {arg_lexeme}")

        try:
            return int(arg_lexeme, base)

        except ValueError as e:
            raise ByteLangError(f"NotValid value '{arg_lexeme}' error: {e}")

    def instruction(self, statement: Statement, inline_last: bool = False) -> StatementUnit:
        instruction = self.environment.getPackage().INSTRUCTIONS.get(statement.lexeme)

        if instruction is None:
            self.environment.statementError("InvalidInstruction", statement)

        if instruction.can_inline is False and inline_last is True:
            self.environment.statementError("CantInline", statement)

        if len(instruction.signature) != len(statement.args):
            self.environment.statementError("InvalidArgument", statement)

        self.mark_offset += instruction.getSize(self.environment.getPlatform(), inline_last)

        return StatementUnit(
            instruction,
            tuple(self.getValue(arg) for arg in statement.args),
            inline_last
        )

    def directive(self, statement: Statement) -> StatementUnit | None:
        if (d := self.DIRECTIVES.get(statement.lexeme)) is None:
            self.environment.statementError("InvalidDirective", statement)

        if d.args is not None and len(statement.args) != d.args:
            raise self.environment.statementError("InvalidArgCount", statement)

        return self.DIRECTIVE_CALLBACKS.get(d)(statement)

    def directiveDefineMacro(self, statement):
        name, value = statement.args
        self.environment.program.constants[name] = self.getValue(value)

    def directiveUseInline(self, statement: Statement) -> StatementUnit:
        lexeme, *args = statement.args
        return self.instruction(Statement(StatementType.INSTRUCTION, lexeme, args, statement.line), True)

    def directiveInitPointer(self, statement: Statement):
        ptr_type, ptr_name = statement.args

        if not utils.BytesLegacy.typeExist(ptr_type):
            self.environment.statementError("InvalidType", statement)

        ptr_addr = self.ptr_addr_next

        if ptr_addr < self.environment.getPlatform().DATA.ptr_heap:
            self.environment.statementError("AddressBeforeHeap", statement)

        if (ptr_addr + utils.BytesLegacy.size(ptr_type)) > self.environment.program.heap_size:
            self.environment.statementError("AddressAfterHeap", statement)

        p_vars = self.environment.program.variables

        if ptr_name in p_vars:
            self.environment.statementError("RedefineVariable", statement)

        ret = p_vars[ptr_name] = PointerVariable(ptr_name, ptr_addr, ptr_type)
        self.ptr_addr_next += ret.size(self.environment.getPlatform())

    def directiveSetHeap(self, statement: Statement):
        if self.heap_directive_used:
            self.environment.statementError("ReinitHeap", statement)

        self.heap_directive_used = True
        h = self.environment.program.heap_size = self.getValue(statement.args[0])
        self.mark_offset += h

        if not (0 < h < self.MAX_HEAP_SIZE):
            self.environment.statementError("InvalidHeapSize", statement)

    def directiveSetPointer(self, statement: Statement):
        name, value = statement.args

        if (var := self.environment.program.variables.get(name)) is None:
            self.environment.statementError("VariableNotDefined", statement)

        var_min, var_max = utils.BytesLegacy.typeRange(var.type)

        if not (var_min <= (value := self.getValue(value)) <= var_max):
            raise self.environment.statementError(f"NotInRange[{var_min};{var_max}]", statement)

        if var.has_static_set:
            self.environment.statementError("VariableReinit", statement)

        var.set(value)


class Compiler:
    """Компилятор в байткод"""

    def __init__(self, environment: Environment):
        self.environment = environment

    def run(self, statementsUnits: Iterable[StatementUnit]) -> bytes:
        ret = self.getHeap() + self.getProgram(statementsUnits)

        if (L := len(ret)) > (max_len := self.environment.getPlatform().DATA.prog_len):
            raise ByteLangError(f"Program too long ({L}/{max_len})")

        return ret

    def getProgram(self, statementsUnits):
        program = bytes()
        for unit in statementsUnits:
            program += unit.pack(self.environment.getPlatform())
        return program

    def getHeap(self):

        heap_ptr = self.environment.getPlatform().DATA.ptr_heap
        heap_size = self.environment.program.heap_size
        heap = utils.BytesLegacy.pack(utils.BytesLegacy.int(heap_ptr), (heap_size,))

        if heap_size == 0:
            return heap

        heap += bytes(heap_size - heap_ptr)

        heap = list(heap)

        for var in self.environment.program.variables.values():
            var_bytes = list(var.pack(self.environment.getPlatform()))

            for i, b in enumerate(var_bytes):
                heap[i + var.ptr] = b

        return bytes(heap)
