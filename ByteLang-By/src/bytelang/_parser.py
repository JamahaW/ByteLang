"""
ByteLang Parser
"""
from __future__ import annotations

from _ast import Expression
from dataclasses import dataclass
from typing import Callable
from typing import ClassVar
from typing import Final
from typing import Optional
from typing import Sequence

from bytelang._ast import Declaration
from bytelang._ast import Field
from bytelang._ast import FieldDeclaration
from bytelang._ast import Identifier
from bytelang._ast import Module
from bytelang._ast import PublicDeclaration
from bytelang._ast import Symbol
from bytelang._ast import SymbolDeclaration
from bytelang._ast import Type
from bytelang._ast import Variable
from bytelang._ast import VariableDeclaration
from bytelang._stream import OutputStream
from bytelang._token import Token
from bytelang._token import TokenType


class Parser:
    """ByteLang parser"""

    # types

    @dataclass(frozen=True)
    class Error:
        """Parsing Error"""
        message: str
        token: Optional[Token]

    # front-end

    _keyword_public: ClassVar = "pub"
    _keyword_variable: ClassVar = "var"
    _keyword_symbol_define: ClassVar = "def"

    def __init__(self, tokens: Sequence[Token]) -> None:
        self._tokens: Final = OutputStream(tokens)
        self._errors: Final = list[Parser.Error]()

    def errors(self) -> Sequence[Error]:
        """Get possible errors"""
        return self._errors

    def identifier(self) -> Optional[Identifier]:
        """Parse identifier"""
        token: Optional[Token[str]] = self._consume(TokenType.identifier)

        if token is None:
            return None

        return Identifier(main_token=token, id=token.value)

    def symbol(self) -> Optional[Symbol]:
        """Parse symbol"""
        token = self._consume_keyword(self._keyword_symbol_define)

        if token is None:
            return None

        identifier = self.identifier()

        if identifier is None:
            return None

        if self._consume(TokenType.operator_assign) is None:
            return None

        expression = self.expression()

        if expression is None:
            return None

        return Symbol(token, identifier, expression)

    def variable(self) -> Optional[Variable]:
        """Parse variable"""
        token = self._consume_keyword(self._keyword_variable)

        if token is None:
            return None

        field = self.field()

        if field is None:
            return None

        if self._consume(TokenType.operator_assign) is None:
            return None

        expression = self.expression()

        if expression is None:
            return None

        return Variable(token, field, expression)

    def field(self) -> Optional[Field]:
        """Parse field"""
        identifier = self.identifier()

        if identifier is None:
            return None

        if self._consume(TokenType.delimiter_colon) is None:
            return None

        _type = self.type()

        if _type is None:
            return None

        return Field(identifier.main_token, identifier, _type)

    def public_declaration(self) -> Optional[PublicDeclaration]:
        """parse public declaration"""
        token = self._consume_keyword(self._keyword_public)

        if Token is None:
            return None

        declaration = self.declaration()

        if declaration is None:
            return None

        return PublicDeclaration(token, declaration)

    def symbol_declaration(self) -> Optional[SymbolDeclaration]:
        """parse symbol declaration"""
        symbol = self.symbol()

        if symbol is None:
            return None

        return SymbolDeclaration(symbol.main_token, symbol)

    def variable_declaration(self) -> Optional[VariableDeclaration]:
        """parse symbol declaration"""
        variable = self.variable()

        if variable is None:
            return None

        return VariableDeclaration(variable.main_token, variable)

    def field_declaration(self) -> Optional[FieldDeclaration]:
        """parse field declaration"""
        field = self.field()

        if field is None:
            return None

        return FieldDeclaration(field.main_token, field)

    def declaration(self) -> Optional[Declaration]:
        """parse declaration"""

        token = self._consume(TokenType.identifier)

        if token.value == self._keyword_public:
            return self.public_declaration()

        if token.value == self._keyword_variable:
            return self.variable_declaration()

        return self.field_declaration()

    def module(self) -> Optional[Module]:
        """Parse input tokens into Bytelang AST Module Node"""
        raise NotImplementedError

    def type(self) -> Optional[Type]:
        """parse type"""
        raise NotImplementedError

    def expression(self) -> Optional[Expression]:
        """Parse expression node"""
        raise NotImplementedError

    # back-end

    def _add_error(self, message: str) -> None:
        """Add error at last token"""
        self._errors.append(self.Error(message, self._tokens.peek()))

    # back-end: parsing process methods

    def _match(self, expected_type: TokenType) -> Optional[Token]:
        """
        Checks peek token
        :param expected_type:
        :return:
        """
        token = self._tokens.peek()

        if token is None:
            self._add_error(f"Expected {expected_type}, got EOF")
            return None

        if token.type != expected_type:
            self._add_error(f"Expected {expected_type}, got {token.type}")
            return None

        return token

    def _consume(self, expected_type: TokenType) -> Optional[Token]:
        """
        Eat token of expected type or none and write error
        :param expected_type:
        :return: Token with expected type or None
        """
        token = self._tokens.next()

        if token is None:
            self._add_error(f"Expected {expected_type}, got EOF")
            return None

        if token.type != expected_type:
            self._add_error(f"Expected {expected_type}, got {token.type}")
            return None

        return token

    def _consume_keyword(self, expected_identifier: str) -> Optional[Token]:
        """
        Eat identifier token with expected identifier value
        :param expected_identifier:
        :return: Token with Identifier type and expected value or none
        """
        token = self._consume(TokenType.identifier)

        if token is None:
            return None

        if token.value != expected_identifier:
            self._add_error(f"'{token.value}' not an expected keyword '{expected_identifier}'")
            return None

        return token

    def _parse_list[T](
            self,
            element_parser: Callable[[], Optional[T]],
            delimiter: TokenType,
            terminator: TokenType,
            ignore: Optional[TokenType]
    ) -> Sequence[T]:
        pass
