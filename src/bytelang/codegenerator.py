from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from typing import Iterable
from typing import Optional

from bytelang.content import Environment
from bytelang.content import EnvironmentInstruction
from bytelang.content import InstructionArgument
from bytelang.content import PrimitiveType
from bytelang.content import PrimitiveWriteType
from bytelang.handlers import BasicErrorHandler
from bytelang.registries import EnvironmentsRegistry
from bytelang.registries import PrimitiveTypeRegistry
from bytelang.statement import ArgumentValueType
from bytelang.statement import Statement
from bytelang.statement import StatementType
from bytelang.statement import UniversalArgument
from bytelang.tools import Filter
from bytelang.tools import ReprTool


@dataclass(frozen=True, kw_only=True)
class CodeInstruction:
    """Инструкция кода"""

    instruction: EnvironmentInstruction
    """Используемая инструкция"""
    arguments: tuple[bytes, ...]
    """Запакованные аргументы"""

    def write(self, instruction_index: PrimitiveType) -> bytes:
        return instruction_index.write(self.instruction.index) + b"".join(self.arguments)

    def __repr__(self) -> str:
        args_s = ReprTool.iter((
            f"({arg_t}){ReprTool.prettyBytes(arg_v)}"
            for arg_t, arg_v in zip(self.instruction.arguments, self.arguments)
        ), l_paren="{ ", r_paren=" }")
        return f"{self.instruction.generalInfo()} {args_s}"


@dataclass(frozen=True)
class DirectiveArgument:
    """Параметры аргумента директивы"""

    name: str
    """Имя параметра (для вывода ошибок)"""
    type: ArgumentValueType
    """Маска принимаемых типов"""


@dataclass(frozen=True)
class Directive:
    """Конфигурация директивы"""

    handler: Callable[[Statement], None]
    """Обработчик директивы"""

    arguments: tuple[DirectiveArgument, ...]
    """Параметры аргументов."""


@dataclass(frozen=True, kw_only=True)
class Variable:
    """Переменная программы"""

    address: int
    """адрес"""
    identifier: str
    """Идентификатор"""
    primitive: PrimitiveType
    """Примитивный тип"""
    value: bytes
    """Значение"""

    def write(self, type_index: PrimitiveType) -> bytes:
        return type_index.write(self.primitive.index) + self.value

    def __repr__(self) -> str:
        return f"{self.primitive!s} {self.identifier}@{self.address} = {ReprTool.prettyBytes(self.value)}"


@dataclass(frozen=True, kw_only=True)
class ProgramData:
    environment: Environment
    start_address: int
    variables: tuple[Variable, ...]
    constants: dict[str, UniversalArgument]


class CodeGenerator:
    """
    Исполнитель Директив. # TODO нужен исполнитель директив

    Генератор промежуточного кода.
    Вычисление констант.
    """

    def __init__(self, error_handler: BasicErrorHandler, environments: EnvironmentsRegistry, primitives: PrimitiveTypeRegistry) -> None:
        self.__err = error_handler.getChild(self.__class__.__name__)
        self.__environments = environments
        self.__primitives = primitives

        self.__env: Optional[Environment] = None
        self.__constants = dict[str, UniversalArgument]()
        self.__variables = dict[str, Variable]()

        self.__mark_offset_isolated: Optional[int] = None
        self.__variable_offset: Optional[int] = None

        __DIRECTIVE_ARG_ANY = DirectiveArgument("constant value or identifier", ArgumentValueType.ANY)

        self.__DIRECTIVES: dict[str, Directive] = {
            "env": Directive(self.__directiveSetEnvironment, (
                DirectiveArgument("environment name", ArgumentValueType.IDENTIFIER),
            )),
            "def": Directive(self.__directiveDeclareConstant, (
                DirectiveArgument("constant name", ArgumentValueType.IDENTIFIER),
                __DIRECTIVE_ARG_ANY
            )),
            "ptr": Directive(self.__directiveDeclarePointer, (
                DirectiveArgument("pointer identifier", ArgumentValueType.IDENTIFIER),
                DirectiveArgument("primitive type", ArgumentValueType.IDENTIFIER),
                __DIRECTIVE_ARG_ANY
            )),
        }

        self.__METHOD_BY_TYPE: dict[StatementType, Callable[[Statement], Optional[CodeInstruction]]] = {
            StatementType.DIRECTIVE_USE: self.__processDirective,
            StatementType.MARK_DECLARE: self.__processMark,
            StatementType.INSTRUCTION_CALL: self.__processInstruction
        }

    def __checkArgumentCount(self, statement: Statement, need: tuple) -> None:
        if (need := len(need)) != (got := len(statement.arguments)):
            self.__err.writeStatement(statement, f"Invalid arg count. Need {need} (got {got})")

    def __checkNameAvailable(self, statement: Statement, name: str) -> None:
        if name in self.__constants.keys() or name in self.__env.instructions.keys():
            self.__err.writeStatement(statement, f"Идентификатор {name} уже используется")

    def __checkNameExist(self, statement: Statement, identifier: str) -> None:
        if identifier not in self.__constants.keys():
            self.__err.writeStatement(statement, f"Идентификатор {identifier} не определён")

    def __addConstant(self, statement: Statement, name: str, value: UniversalArgument) -> None:
        self.__err.begin()
        self.__checkNameAvailable(statement, name)

        if value.identifier is not None:
            self.__checkNameExist(statement, value.identifier)

        if self.__err.failed():
            return

        self.__constants[name] = value

    def __writeArgumentFromPrimitive(self, statement: Statement, argument: UniversalArgument, primitive: PrimitiveType) -> Optional[bytes]:
        if argument.identifier:
            self.__checkNameExist(statement, argument.identifier)

            if self.__err.failed():
                return

            return self.__writeArgumentFromPrimitive(statement, self.__constants[argument.identifier], primitive)

        v = argument.exponent if primitive.write_type == PrimitiveWriteType.exponent else argument.integer

        try:
            return primitive.write(v)

        except Exception as e:
            self.__err.writeStatement(statement, f"Не удалось выполнить преобразование: {e}")

    def __writeArgumentFromInstructionArg(self, statement: Statement, i: int, u_arg: UniversalArgument, i_arg: InstructionArgument) -> Optional[bytes]:
        if i_arg.is_pointer and u_arg.identifier not in self.__variables:
            self.__err.writeStatement(statement, f"Аргумент ({i}) Обращение по указателю ({i_arg}) с помощью сырого значения недопустимо")

        return self.__writeArgumentFromPrimitive(statement, u_arg, i_arg.primitive)

    def __directiveSetEnvironment(self, statement: Statement) -> None:
        if self.__env is not None:
            self.__err.writeStatement(statement, "Окружение должно быть выбрано однократно")
            return

        env_name = statement.arguments[0].identifier

        try:
            self.__env = self.__environments.get(env_name)

        except Exception as e:
            self.__err.writeStatement(statement, f"Не удалось загрузить окружение {env_name}\n{e}")

        init_offset = self.__env.profile.pointer_heap.size
        self.__variable_offset = int(init_offset)
        self.__mark_offset_isolated = int(init_offset)

    def __directiveDeclareConstant(self, statement: Statement) -> None:
        name, value = statement.arguments
        self.__addConstant(statement, name.identifier, value)

    def __directiveDeclarePointer(self, statement: Statement) -> None:
        typename, name, init_value = statement.arguments
        name = name.identifier
        self.__err.begin()

        if (primitive := self.__primitives.get(typename.identifier)) is None:
            self.__err.writeStatement(statement, f"Unknown primitive type: {primitive}")

        self.__checkNameAvailable(statement, name)

        if init_value.identifier:
            self.__checkNameExist(statement, init_value.identifier)

        if self.__variable_offset is None:
            self.__err.writeStatement(statement, "variable offset index undefined. Must select env")

        arg_value = self.__writeArgumentFromPrimitive(statement, init_value, primitive)

        if self.__err.failed():
            return

        self.__addConstant(statement, name, UniversalArgument.fromInteger(self.__variable_offset))

        self.__variables[name] = Variable(
            address=self.__variable_offset,
            identifier=name,
            primitive=primitive,
            value=arg_value
        )

        self.__variable_offset += primitive.size + self.__env.profile.pointer_heap.size

    def __processDirective(self, statement: Statement) -> None:
        if (directive := self.__DIRECTIVES.get(statement.head)) is None:
            self.__err.writeStatement(statement, f"Unknown directive: {statement.head}")
            return

        self.__err.begin()
        self.__checkArgumentCount(statement, directive.arguments)

        self.__err.begin()

        for i, (d_arg, s_arg) in enumerate(zip(directive.arguments, statement.arguments)):
            d_arg: DirectiveArgument
            s_arg: UniversalArgument

            if s_arg.type not in d_arg.type:
                self.__err.writeStatement(statement, f"Incorrect Directive Argument at {i + 1} type: {s_arg.type}. expected: {d_arg.type} ({d_arg.name})")

        if not self.__err.failed():
            directive.handler(statement)

    def __getMarkOffset(self) -> int:
        return self.__variable_offset + self.__mark_offset_isolated

    def __processMark(self, statement: Statement) -> None:
        # TODO отлавливать неверное использование меток (__mark_offset < __variable_offset)
        self.__addConstant(statement, statement.head, UniversalArgument.fromInteger(self.__getMarkOffset()))

    def __processInstruction(self, statement: Statement) -> Optional[CodeInstruction]:
        self.__err.begin()

        if self.__env is None:
            self.__err.writeStatement(statement, "no env (need) select env")
            return

        if (instruction := self.__env.instructions.get(statement.head)) is None:
            self.__err.writeStatement(statement, f"unknown instruction: {statement.head}")
            return

        self.__err.begin()
        self.__checkArgumentCount(statement, instruction.arguments)

        if self.__err.failed():
            return

        self.__err.begin()

        code_ins_args = tuple(
            self.__writeArgumentFromInstructionArg(statement, i + 1, s_arg, i_arg)
            for i, (i_arg, s_arg) in enumerate(zip(instruction.arguments, statement.arguments))
        )

        if self.__err.failed():
            return

        self.__mark_offset_isolated += instruction.size
        return CodeInstruction(instruction=instruction, arguments=code_ins_args)

    def __reset(self) -> None:
        self.__constants.clear()
        self.__variables.clear()
        self.__mark_offset_isolated = None
        self.__variable_offset = None
        self.__env = None

    def run(self, statements: Iterable[Statement]) -> tuple[tuple[CodeInstruction, ...], Optional[ProgramData]]:
        self.__reset()
        return (
            tuple(Filter.notNone(self.__METHOD_BY_TYPE[s.type](s) for s in statements)),
            self.getProgramData()
        )

    # noinspection PyTypeChecker
    def getProgramData(self) -> Optional[ProgramData]:
        if self.__env is None:
            self.__err.write("must select env")
            return

        return ProgramData(
            environment=self.__env,
            start_address=self.__variable_offset,
            variables=tuple(self.__variables.values()),
            constants=self.__constants
        )
