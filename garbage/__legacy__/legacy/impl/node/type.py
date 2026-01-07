from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

from bytelang.legacy.abc.parser import Parser
from bytelang.legacy.abc.profiles import TypeProfile
from bytelang.legacy.core.result import LogResult
from bytelang.legacy.core.result import ResultAccumulator
from bytelang.legacy.core.tokens import TokenType
from bytelang.legacy.impl.node.expression import Expression
from bytelang.legacy.impl.node.expression import HasExistingID
from bytelang.legacy.impl.node.expression import Identifier
from bytelang.legacy.impl.node.super import SuperNode
from bytelang.legacy.impl.profiles.type import ArrayTypeProfile
from bytelang.legacy.impl.profiles.type import PointerTypeProfile
from bytelang.legacy.impl.semantizer.common import SuperSemanticContext


class TypeNode(SuperNode[SuperSemanticContext, TypeProfile, 'Type'], ABC):
    """Узел типа"""

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[TypeNode]:
        match parser.tokens.peek().item_type:
            case TokenType.Star:
                return PointerTypeNode.parse(parser)

            case TokenType.OpenSquare:
                return ArrayTypeNode.parse(parser)

        return PureTypeNode.parse(parser)

    @abstractmethod
    def accept(self, context: SuperSemanticContext) -> LogResult[TypeProfile]:
        pass


@dataclass(frozen=True)
class PureTypeNode(TypeNode, HasExistingID):
    """Чистый тип"""

    def accept(self, context: SuperSemanticContext) -> LogResult[TypeProfile]:
        return context.getTypes().get(self.identifier.id)

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[TypeNode]:
        """Создать чистый тип на основе идентификатора"""
        return Identifier.parse(parser).map(lambda ok: cls(ok))


@dataclass(frozen=True)
class PointerTypeNode(TypeNode):
    """Тип Указателя"""

    pointer: TypeNode
    """Тип указателя"""

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[TypeNode]:
        parser.tokens.next()
        return TypeNode.parse(parser).map(lambda t: cls(t))

    def accept(self, context: SuperSemanticContext) -> LogResult[TypeProfile]:
        ret = ResultAccumulator()
        _type_profile = self.pointer.accept(context)
        return ret.map(lambda _: PointerTypeProfile(_type_profile.unwrap()))


@dataclass(frozen=True)
class ArrayTypeNode(TypeNode):
    """Тип Массив"""

    type: TypeNode
    """Тип элементов массива"""
    length: Expression
    """Выражение, определяющее длину массива"""

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[TypeNode]:
        parser.tokens.next()

        ret = ResultAccumulator()

        expr = ret.put(Expression.parse(parser))
        ret.put(parser.consume(TokenType.CloseSquare))
        _type = ret.put(TypeNode.parse(parser))

        return ret.map(lambda _: cls(_type.unwrap(), expr.unwrap()))

    def accept(self, context: SuperSemanticContext) -> LogResult[TypeProfile]:
        ret = ResultAccumulator()

        item_type_profile = ret.put(self.type.accept(context))
        array_length = ret.put(self.length.accept(context))

        return ret.map(lambda _: ArrayTypeProfile(item_type_profile.unwrap(), array_length.unwrap().getValue()))


@dataclass(frozen=True)
class Field(SuperNode[SuperSemanticContext, tuple[str, TypeProfile], "Field"], HasExistingID):
    """Узел объявления поля"""

    type: TypeNode
    """Тип поля"""

    def accept(self, context: SuperSemanticContext) -> LogResult[tuple[str, TypeProfile]]:
        ret = ResultAccumulator()
        type_profile = ret.put(self.type.accept(context))
        return ret.map(lambda _: (self.identifier.id, type_profile.unwrap()))

    @classmethod
    def parse(cls, parser: Parser) -> LogResult[Field]:
        """Парсинг токенов в поле"""
        ret = ResultAccumulator()

        name = ret.put(Identifier.parse(parser))
        ret.put(parser.consume(TokenType.Colon))
        pure = ret.put(TypeNode.parse(parser))

        return ret.map(lambda _: cls(name.unwrap(), pure.unwrap()))
