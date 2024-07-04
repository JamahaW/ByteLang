from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from typing import Iterable
from typing import Optional

from bytelang.content import Environment
from bytelang.content import EnvironmentInstruction
from bytelang.handlers import BasicErrorHandler
from bytelang.registries import EnvironmentsRegistry
from bytelang.registries import PrimitiveTypeRegistry
from bytelang.statement import ArgumentValueType
from bytelang.statement import Statement
from bytelang.statement import StatementType
from bytelang.statement import UniversalArgument
from bytelang.tools import Filter


@dataclass(frozen=True, kw_only=True)
class CodeInstruction:
    """Инструкция кода"""

    instruction: EnvironmentInstruction
    """Используемая инструкция"""
    arguments: tuple[bytes, ...]
    """Запакованные аргументы"""


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
        self.__constants = dict[str, UniversalArgument]()

        self.__env: Optional[Environment] = None

        __DIRECTIVE_ARG_ANY = DirectiveArgument("constant value or identifier", ArgumentValueType.ANY)

        self.__DIRECTIVES: dict[str, Directive] = {
            "env": Directive(self.__directiveSetEnvironment, (
                DirectiveArgument("environment name", ArgumentValueType.IDENTIFIER),
            )),
            "def": Directive(self.__directiveConstantDeclare, (
                DirectiveArgument("constant name", ArgumentValueType.IDENTIFIER),
                __DIRECTIVE_ARG_ANY
            )),
            "ptr": Directive(self.__directivePointerDeclare, (
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

    def __directiveSetEnvironment(self, statement: Statement) -> None:
        print("__directiveSetEnvironment", statement)

    def __directiveConstantDeclare(self, statement: Statement) -> None:
        print("__directiveConstantDeclare", statement)

    def __directivePointerDeclare(self, statement: Statement) -> None:
        print("__directivePointerDeclare", statement)

    def __processDirective(self, statement: Statement) -> None:
        if (directive := self.__DIRECTIVES.get(statement.head)) is None:
            self.__err.writeStatement(statement, f"Unknown directive: {statement.head}")
            return

        if (need := len(directive.arguments)) != (got := len(statement.arguments)):
            self.__err.writeStatement(statement, f"Invalid arg count need: {need} (got: {got})")
            return

        self.__err.begin()

        for i, (d_arg, s_arg) in enumerate(zip(directive.arguments, statement.arguments)):
            d_arg: DirectiveArgument
            s_arg: UniversalArgument

            if s_arg.type not in d_arg.type:
                self.__err.writeStatement(statement, f"Incorrect Directive Argument at {i} type: {s_arg.type}. expected: {d_arg.type}")

        if not self.__err.failed():
            directive.handler(statement)

    def __processMark(self, statement: Statement) -> None:
        pass

    def __processInstruction(self, statement: Statement) -> CodeInstruction:
        pass

    def __reset(self) -> None:
        self.__constants.clear()

    def run(self, statements: Iterable[Statement]) -> Iterable[CodeInstruction]:
        self.__reset()
        return Filter.notNone(self.__METHOD_BY_TYPE[s.type](s) for s in statements)
