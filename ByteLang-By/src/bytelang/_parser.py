from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import field
from typing import Callable
from typing import Final
from typing import Optional
from typing import Self
from typing import Sequence

from bytelang._token import Token
from bytelang._token import TokenType


@dataclass(frozen=True)
class Node(ABC):
    """ByteLang AST Node"""

    token: Token = field(repr=False)

    @classmethod
    @abstractmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        """apply parser on node"""


class ValueNode(Node):
    """Value"""

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        pass


@dataclass(frozen=True)
class LiteralValueNode[T: (None, int, float, str, tuple)](ValueNode):
    value: T

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        pass


@dataclass(frozen=True)
class IdentifierNode(ValueNode):
    """Identifier"""

    name: str

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        token: Optional[Token[str]] = parser.consume(TokenType.identifier)

        if token:
            return cls(token, token.value)

        return None


@dataclass(frozen=True)
class TypeNode(ValueNode):
    """
    Type
    <type>
    """

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        pass


@dataclass(frozen=True)
class _PureTypeNode(TypeNode):
    """
    <id>
    """

    identifier: IdentifierNode

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        _id = IdentifierNode.parse(parser)

        if not _id:
            return None

        return cls(parser.peek(), _id)


@dataclass(frozen=True)
class _PointerTypeNode(TypeNode):
    """
    *<type>
    """

    type: TypeNode

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        star = parser.consume(TokenType.delimiter_star)

        if not star:
            return None

        _type = TypeNode.parse(parser)

        if not _type:
            return None

        return cls(parser.peek(), _type)


@dataclass(frozen=True)
class _ArrayKindTypeNode(TypeNode):
    """
    [ ... ]<type>
    """

    type: TypeNode

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        _open = parser.consume(TokenType.bracket_open_square)

        if not _open:
            return None

        _next = parser.consume(TokenType.bracket_close_square)

        if _next:
            return _SliceTypeNode.parse(parser)

        return _ArrayTypeNode.parse(parser)


@dataclass(frozen=True)
class _SliceTypeNode(_ArrayKindTypeNode):
    """
    []<type>
    """

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        _type = TypeNode.parse(parser)

        if not _type:
            return None

        return cls(parser.peek(), _type)


@dataclass(frozen=True)
class _ArrayTypeNode(_ArrayKindTypeNode):
    """
    [ <value(literal(int))> ] <type>
    """

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        _len: Optional[LiteralValueNode[int]] = LiteralValueNode.parse(parser)

        if not _len:
            return None

        _close = parser.consume(TokenType.bracket_close_square)

        if not _close:
            return None

        _type = TypeNode.parse(parser)

        if not _type:
            return None

        return cls(parser.peek(), _type)


@dataclass(frozen=True)
class FieldNode(Node):
    """

    <id> : <type>

    """

    identifier: IdentifierNode
    type: TypeNode

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        identifier = IdentifierNode.parse(parser)

        if not identifier:
            return None

        token = parser.consume(TokenType.delimiter_colon)

        if not token:
            return None

        _type = TypeNode.parse(parser)

        if not _type:
            return None

        return cls(token, identifier, _type)


class FunctionCallNode(Node):
    """
    Function call

    <id> ( <value> , <value> , ... )
    """

    instruction: IdentifierNode
    arguments: Sequence[ValueNode]

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        pass


class KeywordNode(Node, ABC):
    """Bytelang Keyword node"""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """name of keyword"""

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        keyword_id: Optional[Token[str]] = parser.consume(TokenType.identifier)

        if not keyword_id:
            return None

        keyword = cls.__keywords.get(keyword_id.value)

        if not keyword:
            parser.add_error(f"unknown keyword: '{keyword_id}'")
            return None

        return keyword.parse(parser)

    @staticmethod
    def _keywords() -> set[type[KeywordNode]]:
        return {
            ConstantDeclarationNode,
            ImportNode,
            VariableDeclarationNode,
            FunctionDeclarationNode,
            PublicNode,
            ReturnNode,
            StructNode,
            UndefinedNode
        }

    __keywords = {
        keyword.name(): keyword
        for keyword in _keywords()
    }


@dataclass(frozen=True)
class UndefinedNode(KeywordNode, LiteralValueNode[None]):
    """undefined"""

    @classmethod
    def name(cls) -> str:
        return "undefined"

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        return cls(parser.peek(), None)


@dataclass(frozen=True)
class ConstantDeclarationNode(KeywordNode):
    """
    Declares Constant

    const <id> = <value>
    """

    identifier: IdentifierNode
    value: ValueNode

    @classmethod
    def name(cls) -> str:
        return "const"

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        identifier = IdentifierNode.parse(parser)
        token = parser.consume(TokenType.delimiter_assign)
        value = ValueNode.parse(parser)
        return cls(token, identifier, value)


@dataclass(frozen=True)
class ImportNode(KeywordNode):
    """
    Imports module

    import <id>
    """

    target: IdentifierNode

    @classmethod
    def name(cls) -> str:
        return "import"

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        target = IdentifierNode.parse(parser)

        if not target:
            return None

        return cls(parser.peek(), target)


@dataclass(frozen=True)
class ReturnNode(KeywordNode):
    """
    Function return

    f() -> void:
        return

    f() -> T:
        return <value(T)>
    """

    result: ValueNode

    @classmethod
    def name(cls) -> str:
        return "return"

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        pass


@dataclass(frozen=True)
class VariableDeclarationNode(KeywordNode, ABC):
    """
    Declares Variable

    var <field> = <value>
    """

    field: FieldNode
    init: ValueNode

    @classmethod
    def name(cls) -> str:
        return "var"

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        pass


@dataclass(frozen=True)
class FunctionDeclarationNode(KeywordNode):
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
    def parse(cls, parser: Parser) -> Optional[Self]:
        pass


@dataclass(frozen=True)
class _NativeFunctionKeywordDeclarationNode(FunctionDeclarationNode):
    """
    Native Function

    fn <id> ( <field> , <field> , ... ) = <value(literal(int))>
    """

    bind: LiteralValueNode[int]

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        pass


@dataclass(frozen=True)
class _UserFunctionKeywordDeclarationNode(FunctionDeclarationNode):
    """
    User Function

    fn <id> ( <field> , <field> , ... ) {
        <inst-call>

        const ...
    }
    """

    body: Sequence[FunctionCallNode]
    constants: Sequence[ConstantDeclarationNode]

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        pass


@dataclass(frozen=True)
class StructNode(KeywordNode, TypeNode):
    """
    Struct

    struct {
        <field>, <field>,
        <field> ...

        <keyword...>
    }
    """

    fields: Sequence[FieldNode]
    keywords: Sequence[KeywordNode]

    @classmethod
    def name(cls) -> str:
        return "struct"


@dataclass(frozen=True)
class PublicNode(KeywordNode):
    """
    Static variable

    pub <id> ...
    """

    keyword: KeywordNode

    @classmethod
    def name(cls) -> str:
        return "pub"

    @classmethod
    def parse(cls, parser: Parser) -> Optional[Self]:
        keyword = KeywordNode.parse(parser)

        if not keyword:
            return None

        return cls(parser.peek(), keyword)


@dataclass(frozen=True)
class ModuleNode(Node):
    """ByteLang Module"""

    keywords: Sequence[KeywordNode]

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
        self._tokens: Final = tokens
        self._position = 0
        self._errors: Final = list[Parser.Error]()

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

    def advance(self) -> Optional[Token]:
        """Перейти к следующему токену"""
        if self._position >= len(self._tokens):
            self._add_error("Unexpected end of file")
            return None

        token = self._tokens[self._position]
        self._position += 1

        return token

    def consume(self, expected_type: TokenType) -> Optional[Token]:
        """Съесть токен ожидаемого типа"""
        token = self.peek()

        if token is None:
            self._add_error(f"Expected {expected_type}, got EOF")
            return None

        if token.type != expected_type:
            self._add_error(f"Expected {expected_type}, got {token.type}")
            return None

        return self.advance()

    def match(self, token_type: TokenType) -> bool:
        """Проверить совпадение без продвижения"""
        token = self.peek()
        return token is not None and token.type == token_type

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

    def add_error(self, message: str) -> None:
        self._errors.append(self.Error(message, self.peek()))
