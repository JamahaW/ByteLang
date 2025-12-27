from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable
from typing import Optional
from typing import Self
from typing import Sequence

from bytelang import TokenType
from bytelang._token import Token


class Node(ABC):
    """ByteLang AST Node"""

    @classmethod
    @abstractmethod
    def parse(cls, parser: Parser) -> Self:
        """apply parser on node"""


class ValueNode(Node):
    """Value"""

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


@dataclass(frozen=True)
class LiteralValueNode[T: (int, float, str)](ValueNode):
    value: T

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


@dataclass(kw_only=True, frozen=True)
class IdentifierValueNode(ValueNode):
    """Identifier"""

    name: str

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


class TypeNode(ValueNode):
    """Type"""

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


@dataclass(kw_only=True, frozen=True)
class FieldNode(Node):
    identifier: IdentifierValueNode
    type: TypeNode

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


class InstructionCallNode(Node):
    """
    Instruction call

    <id> ( <value> , <value> , ... )
    """

    instruction: IdentifierValueNode
    arguments: Sequence[ValueNode]

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


class DeclarationNode(Node, ABC):
    """Bytelang Declaration Keyword node"""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """name of keyword"""


@dataclass(kw_only=True, frozen=True)
class ConstantDeclarationNode(DeclarationNode):
    """
    Defines constant

    const <id> = <value>
    """

    identifier: IdentifierValueNode
    value: ValueNode

    @classmethod
    def name(cls) -> str:
        return "const"

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


@dataclass(kw_only=True, frozen=True)
class ImportNode(DeclarationNode):
    """
    Imports module

    import <id>
    """

    target: IdentifierValueNode

    @classmethod
    def name(cls) -> str:
        return "import"

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


@dataclass(kw_only=True, frozen=True)
class VariableDeclarationNode(DeclarationNode, ABC):
    """
    Declares Variable

    var <field> ...

    """

    field: FieldNode

    @classmethod
    def name(cls) -> str:
        return "var"

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


class _DynamicVariableDeclarationNode(VariableDeclarationNode):
    """
    Dynamic variable (in function)

    var <field>
    """

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


@dataclass(kw_only=True, frozen=True)
class _StaticVariableDeclarationNode(VariableDeclarationNode):
    """
    Static variable

    var <field> = <value>
    """

    value: ValueNode

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


@dataclass(kw_only=True, frozen=True)
class FunctionDeclarationNode(DeclarationNode):
    """
    Function

    fn <id> ( <field> , <field> , ... )
    """

    arguments: Sequence[FieldNode]

    result_type: TypeNode

    @classmethod
    def name(cls) -> str:
        return "fn"

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


@dataclass(kw_only=True, frozen=True)
class _NativeFunctionKeywordDeclarationNode(FunctionDeclarationNode):
    """
    Native Function

    fn <id> ( <field> , <field> , ... ) = <value(literal(int))>
    """

    bind: LiteralValueNode[int]

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


@dataclass(kw_only=True, frozen=True)
class _UserFunctionKeywordDeclarationNode(FunctionDeclarationNode):
    """
    User Function

    fn <id> ( <field> , <field> , ... ) {
        <inst-call>

        const ...
    }
    """

    body: Sequence[InstructionCallNode]
    constants: Sequence[ConstantDeclarationNode]

    @classmethod
    def parse(cls, parser: Parser) -> Self:
        pass


@dataclass(kw_only=True, frozen=True)
class StructNode(DeclarationNode, TypeNode):
    """
    Struct

    struct {
        <field>, <field>,
        <field> ...


        fn ...
        const ...
    }
    """

    fields: Sequence[FieldNode]
    functions: Sequence[FunctionDeclarationNode]
    constants: Sequence[ConstantDeclarationNode]

    @classmethod
    def name(cls) -> str:
        return "struct"


@dataclass(kw_only=True, frozen=True)
class PublicNode(DeclarationNode):
    """
    Static variable

    pub <id> ...
    """

    @classmethod
    def name(cls) -> str:
        return "pub"

    @classmethod
    def parse(cls, parser: Parser) -> PublicNode:
        pass


@dataclass(kw_only=True, frozen=True)
class ModuleNode(Node):
    """ByteLang Module"""

    keywords: Sequence[DeclarationNode]

    @classmethod
    def parse(cls, parser: Parser) -> ModuleNode:
        pass


class Parser:
    """ByteLang parser"""

    @dataclass(frozen=True)
    class Error:
        """ByteLang Parsing Error"""

        message: str
        token: Optional[Token]

    def __init__(self, tokens: Sequence[Token]) -> None:
        self._tokens = tokens
        self._position = 0
        self._errors = list[Parser.Error]()

    def errors(self) -> Sequence[Error]:
        """Get available parsing errors"""
        return self._errors

    def run(self) -> Optional[ModuleNode]:
        """Parse and get AST"""
        node = ModuleNode.parse(self)

        if self._errors:
            return None

        return node

    def peek(self) -> Optional[Token]:
        """Посмотреть текущий токен"""
        if self._position >= len(self._tokens):
            return None

        return self._tokens[self._position]

    def advance(self) -> Token:
        """Перейти к следующему токену"""
        if self._position >= len(self._tokens):
            self._add_error("Unexpected end of file")

        token = self._tokens[self._position]
        self._position += 1

        return token

    def consume(self, expected_type: TokenType) -> Token:
        """Съесть токен ожидаемого типа"""
        token = self.peek()

        if token is None:
            self._add_error(f"Expected {expected_type}, got EOF")

        if token.type != expected_type:
            self._add_error(f"Expected {expected_type}, got {token.type}")

        return self.advance()

    def match(self, token_type: TokenType) -> bool:
        """Проверить совпадение без продвижения"""
        token = self.peek()
        return token is not None and token.type == token_type

    def expect_identifier(self, value: str = None) -> Token:
        """Ожидать идентификатор (опционально с конкретным значением)"""
        token = self.consume(TokenType.identifier)

        if value is not None and token.value != value:
            self._add_error(f"Expected identifier '{value}', got '{token.value}'")

        return token

    def parse_list[T](
            self,
            element_parser: Callable[[Parser], T],
            delimiter: TokenType,
            end_marker: TokenType,
    ) -> Sequence[T]:
        """Парсинг списка элементов с разделителями"""
        elements = list[T]()

        if self.match(end_marker):
            self.advance()
            return elements

        while True:
            elements.append(element_parser(self))

            if self.match(end_marker):
                self.advance()
                break

            if not self.match(delimiter):
                self._add_error(f"Expected {delimiter} or {end_marker}, got {self.peek().type}")
                break

            self.advance()

            if self.match(end_marker):
                self.advance()
                break

        return elements

    def _add_error(self, message: str) -> None:
        self._errors.append(self.Error(message, self.peek()))
