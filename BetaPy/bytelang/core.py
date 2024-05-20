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
        self.init = False

    def set(self, value: int):
        self.value = value
        self.init = True

    def __repr__(self):
        return f"({self.type}*) {self.name}#{self.ptr} = {self.value}"


@dataclass(init=False)
class ProgramData:
    heap_len: int = 0
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


class Parser:

    def __init__(self, environment: Environment):
        self.environment = environment
        self.mark_offset: int = 0

        self.heap_directive_used = False
        self.ptr_heap_max: int = 0

    def run(self, statements: Iterable[Statement]) -> Iterable[StatementUnit]:
        self.mark_offset += self.environment.getPlatform().DATA.ptr_heap
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

        try:
            return int(arg_lexeme)  # ничего не было найдено, возможно это число

        except ValueError as e:
            raise ByteLangError(f"NotValid value '{arg_lexeme}'")

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
        divs = self.environment.DIRECTIVE

        # TODO arg len check

        match statement.lexeme:
            case divs.SET_HEAP.name:
                self.directiveSetHeap(statement)

            case divs.DEFINE_MACRO.name:
                self.directiveDefineMacro(statement)

            case divs.INIT_POINTER.name:
                self.directiveInitPointer(statement)

            case divs.SET_POINTER.name:
                self.directiveSetPointer(statement)

            case divs.USE_INLINE.name:
                return self.directiveInline(statement)

            case _:
                self.environment.statementError("InvalidDirective", statement)

    def directiveDefineMacro(self, statement):
        name, value = statement.args
        self.environment.program.constants[name] = self.getValue(value)

    def directiveInline(self, statement: Statement) -> StatementUnit:
        lexeme, *args = statement.args
        return self.instruction(Statement(StatementType.INSTRUCTION, lexeme, args, statement.line), True)

    def directiveInitPointer(self, statement: Statement):
        ptr_type, ptr_name, ptr_addr = statement.args

        if not utils.Bytes.typeExist(ptr_type):
            self.environment.statementError("InvalidType", statement)

        ptr_addr = self.getValue(ptr_addr)

        if ptr_addr > self.ptr_heap_max:
            self.environment.statementError("InvalidAddress", statement)

        p_vars = self.environment.program.variables

        if ptr_name in p_vars:
            self.environment.statementError("RedefineVariable", statement)

        p_vars[ptr_name] = PointerVariable(ptr_name, ptr_addr, ptr_type)

    def directiveSetHeap(self, statement: Statement):
        if self.heap_directive_used:
            self.environment.statementError("ReinitHeap", statement)

        self.heap_directive_used = True
        self.ptr_heap_max = self.environment.program.heap_len = self.getValue(statement.args[0])
        self.mark_offset += self.ptr_heap_max

        if self.ptr_heap_max < 0:
            self.environment.statementError("InvalidHeapSize", statement)

    def directiveSetPointer(self, statement: Statement):
        name, value = statement.args

        if (var := self.environment.program.variables.get(name)) is None:
            self.environment.statementError("VariableNotDefined", statement)

        var_min, var_max = utils.Bytes.typeRange(var.type)

        if not (var_min <= (value := self.getValue(value)) <= var_max):
            raise self.environment.statementError(f"NotInRange[{var_min};{var_max}]", statement)

        if var.init:
            self.environment.statementError("VariableReinit", statement)

        var.set(value)


class Compiler:

    def __init__(self, environment: Environment):
        self.environment = environment

    def run(self) -> bytes:
        pass
