"""Общеиспользуемые узлы АСД (Package, Source)"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Iterable
from typing import Mapping
from typing import Optional
from typing import Sequence

from bytelang.legacy.abc.parser import Parser
from bytelang.legacy.abc.profiles import RValueProfile
from bytelang.legacy.abc.registry import Registry
from bytelang.core.ops import Operator
from bytelang.legacy.core.result import ErrOne
from bytelang.legacy.core.result import LogResult
from bytelang.legacy.core.result import Ok
from bytelang.legacy.core.result import ResultAccumulator
from bytelang.legacy.core.tokens import TokenType
from bytelang.legacy.impl.node.super import SuperNode
from bytelang.legacy.impl.profiles.rvalue import InitializerListRV
from bytelang.legacy.impl.semantizer.super import SuperSemanticContext


class Expression(SuperNode[SuperSemanticContext, RValueProfile, "Expression"], ABC):
    """Выражение"""

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[Expression]:
        match parser.tokens.peek().item_type:
            case TokenType.Identifier:
                return Identifier.parse(parser)

            case TokenType.OpenFigure:
                return InitializerList.parse(parser)

            case TokenType.MacroCall:
                return MacroCall.parse(parser)

            case literal_token if literal_token.isLiteral():
                return Literal.parse(parser)

            case not_expression_token:
                return ErrOne(f"Token not an expression: {not_expression_token}")

    @abstractmethod
    def accept(self, context: SuperSemanticContext) -> LogResult[RValueProfile]:
        pass

    @abstractmethod
    def expand(self, table: Mapping[Identifier, Expression]) -> Expression:
        """Развернуть макрос"""


@dataclass(frozen=True)
class InitializerList(Expression):
    """Узел списка инициализации"""

    items: Sequence[Expression]
    """Элементы списка инициализации"""

    def accept(self, context: SuperSemanticContext) -> LogResult[RValueProfile]:
        ret = ResultAccumulator()

        for item in self.items:
            ret.put(item.accept(context))

        return ret.map(lambda items: InitializerListRV(items))

    def expand(self, table: Mapping[Identifier, Expression]) -> InitializerList:
        return InitializerList(tuple(i.expand(table) for i in self.items))

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[InitializerList]:
        items = parser.braceArguments(lambda: Expression.parse(parser), TokenType.OpenFigure, TokenType.CloseFigure)
        return items.map(lambda expressions: cls(expressions))


@dataclass(frozen=True)
class Identifier(Expression):
    """Узел Идентификатора"""

    id: str
    """Имя"""

    def expand(self, table: Mapping[Identifier, Expression]) -> Expression:
        return table.get(self, self)

    def accept(self, context: SuperSemanticContext) -> LogResult[RValueProfile]:
        return context.getConstants().get(self.id)

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[Identifier]:
        """Парсинг токена в узел Идентификатора"""
        return parser.consume(TokenType.Identifier).map(lambda ok: cls(ok.value))


@dataclass(frozen=True)
class Literal[T](Expression):
    """Узел Литерала"""

    value: RValueProfile[T]
    """Значение"""

    def expand(self, table: Mapping[Identifier, Expression]) -> Expression:
        return self

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[Literal[T]]:
        """Парсинг токена в узел Литерала"""
        ret = ResultAccumulator()
        token = parser.tokens.next()

        if (rv_maker := token.item_type.getRightValueMaker()) is None:
            ret.put(ErrOne(f"Ожидался литерал, получено: {token}"))

        return ret.map(lambda _: cls(rv_maker(token.value)))

    def accept(self, context: SuperSemanticContext) -> LogResult[RValueProfile[T]]:
        return Ok(self.value)


@dataclass(frozen=True)
class UnaryOp(Expression):
    """Узел Префиксной Унарной операции"""

    op: Operator
    """Оператор"""
    operand: Expression
    """Операнд"""

    def expand(self, table: Mapping[Identifier, Expression]) -> Expression:
        return UnaryOp(self.op, self.operand.expand(table))

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[UnaryOp]:
        token = parser.tokens.next()

        if (operator := token.item_type.asOperator()) is None:
            return ErrOne(f"Ожидался оператор, получено: {token}")

        return Expression.parse(parser).map(lambda expr: cls(operator, expr))

    def accept[T](self, context: SuperSemanticContext) -> LogResult[RValueProfile[T]]:
        return self.operand.accept(context).andThen(lambda rv: rv.applyUnaryOperator(self.op))


@dataclass(frozen=True)
class BinaryOp(Expression):
    """Узел Бинарной операции"""

    op: Operator
    """Оператор"""
    left: Expression
    """Левый операнд"""
    right: Expression
    """Правый операнд"""

    def expand(self, table: Mapping[Identifier, Expression]) -> Expression:
        return BinaryOp(self.op, self.left.expand(table), self.right.expand(table))

    def accept(self, context: SuperSemanticContext) -> LogResult[RValueProfile]:
        ret = ResultAccumulator()

        a = ret.put(self.left.accept(context))
        b = ret.put(self.right.accept(context))

        if ret.isErr():
            return ret.map()

        c = ret.put(a.unwrap().applyBinaryOperator(b.unwrap(), self.op))

        return ret.map(lambda _: c.unwrap())


@dataclass(frozen=True)
class HasIdentifier:
    """Узел имеет идентификатор"""

    identifier: Identifier
    """Идентификатор узла"""


class HasExistingID(HasIdentifier):
    """Узел имеет идентификатор, уже содержащийся в реестре"""


class HasUniqueID(HasIdentifier):
    """Узел имеет уникальный идентификатор"""

    def checkIdentifier[T](self, registry: Registry[str, T]) -> Optional[str]:
        """Проверить уникальность идентификатора"""
        if registry.has(self.identifier.id):
            return f"{registry} has {self}"


@dataclass(frozen=True)
class MacroCall(Expression):
    """Узел развёртки макроса"""

    macro_id: str
    arguments: Iterable[Expression]

    def expand(self, table: Mapping[Identifier, Expression]) -> Expression:
        return MacroCall(self.macro_id, tuple(arg.expand(table) for arg in self.arguments))

    def accept(self, context: SuperSemanticContext) -> LogResult[RValueProfile]:
        return (
            context.getMacros().get(self.macro_id)
            .andThen(lambda macro: macro.expand(tuple(self.arguments)))
            .andThen(lambda expand: expand.accept(context))
        )

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[MacroCall]:
        ret = ResultAccumulator()

        _id = ret.put(parser.consume(TokenType.MacroCall))
        args = ret.put(parser.braceArguments(lambda: Expression.parse(parser), TokenType.OpenRound, TokenType.CloseRound))

        return ret.map(lambda _: cls(_id.unwrap().value, args.unwrap()))
