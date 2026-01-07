"""
ByteLang Parser
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from typing import ClassVar
from typing import Final
from typing import Optional
from typing import Sequence

from bytelang._ast import AddressTake
from bytelang._ast import ArrayType
from bytelang._ast import Assign
from bytelang._ast import Declaration
from bytelang._ast import Expression
from bytelang._ast import Field
from bytelang._ast import FieldDeclaration
from bytelang._ast import FunctionCall
from bytelang._ast import FunctionCallStatement
from bytelang._ast import FunctionCallValue
from bytelang._ast import FunctionSignature
from bytelang._ast import FunctionSignatureType
from bytelang._ast import FunctionType
from bytelang._ast import Identifier
from bytelang._ast import IntegerLiteral
from bytelang._ast import ListLiteral
from bytelang._ast import LocalSymbol
from bytelang._ast import LocalVariable
from bytelang._ast import Module
from bytelang._ast import Name
from bytelang._ast import PointerType
from bytelang._ast import PublicDeclaration
from bytelang._ast import PureType
from bytelang._ast import RealLiteral
from bytelang._ast import Return
from bytelang._ast import SliceType
from bytelang._ast import Statement
from bytelang._ast import StringLiteral
from bytelang._ast import StructType
from bytelang._ast import Symbol
from bytelang._ast import SymbolDeclaration
from bytelang._ast import Type
from bytelang._ast import UndefinedValue
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

    # static const

    _keyword_public: ClassVar = "pub"
    _keyword_variable: ClassVar = "var"
    _keyword_symbol_define: ClassVar = "def"
    _keyword_undefined_value: ClassVar = "undefined"
    _keyword_function: ClassVar = "fn"
    _keyword_return: ClassVar = "return"
    _keyword_struct: ClassVar = "struct"

    # front-end

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

    def function_signature(self) -> Optional[FunctionSignature]:
        """parse function signature"""
        token = self._tokens.peek()
        arguments = self._parse_brackets_round(self.field)

        if arguments is None:
            return None

        return_type = self.type()

        if return_type is None:
            return None

        return FunctionSignature(token, arguments, return_type)

    def function_call(self) -> Optional[FunctionCall]:
        """parse function call"""

        name = self.name()

        if name is None:
            return None

        arguments = self._parse_brackets_round(self.expression)

        if arguments is None:
            return None

        return FunctionCall(name.main_token, name, arguments)

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
        token = self._tokens.peek()  # Смотрим следующий токен

        if token is None:
            return None

        if token.type != TokenType.identifier:
            self._add_error(f"Expected identifier, got {token.type}")
            return None

        # Смотрим значение токена, но не потребляем его пока
        if token.value == self._keyword_public:
            return self.public_declaration()

        if token.value == self._keyword_variable:
            return self.variable_declaration()

        if token.value == self._keyword_symbol_define:
            return self.symbol_declaration()

        # Для field declaration парсим как обычно
        return self.field_declaration()

    def module(self) -> Optional[Module]:
        """Parse input tokens into Bytelang AST Module Node"""
        declarations = list[Declaration]()
        first: Optional[Token] = None

        while True:
            token = self._tokens.peek()  # Используем peek вместо next

            if token is None:
                break

            if token.type == TokenType.newline:
                self._tokens.next()  # Потребляем newline
                continue

            if first is None:
                first = token

            declaration = self.declaration()

            if declaration is None:
                return None

            declarations.append(declaration)

        return Module(first, declarations)

    def expression(self) -> Optional[Expression]:
        """Dispatch expression parsing based on first token"""
        # Save position for all expression attempts
        self._tokens.push_position()

        # Check first token to determine expression type
        first_token = self._tokens.peek()
        if not first_token:
            self._tokens.pop_position()
            self._add_error("Unexpected EOF in expression")
            return None

        # Address take: &name
        if first_token.type == TokenType.operator_address:
            self._tokens.pop_position()
            return self.address_take()

        # Undefined literal: undefined
        if (first_token.type == TokenType.identifier and
                first_token.value == self._keyword_undefined_value):
            self._tokens.pop_position()
            return self.undefined_value()

        # Integer literal: 123, 0xFF, 0b1010
        if first_token.type in {
            TokenType.literal_int_bin,
            TokenType.literal_int_hex,
            TokenType.literal_int_dec,
            TokenType.literal_int_char,
        }:
            self._tokens.pop_position()
            return self.integer_literal()

        # Real literal: 123.456, 2.0f32
        if first_token.type in {
            TokenType.literal_real,
            TokenType.literal_real_exp,
        }:
            self._tokens.pop_position()
            return self.real_literal()

        # String literal: "hello"
        if first_token.type == TokenType.literal_string:
            self._tokens.pop_position()
            return self.string_literal()

        # List literal: {1, 2, 3}
        if first_token.type == TokenType.bracket_open_figure:
            self._tokens.pop_position()
            return self.list_literal()

        # Try function call as expression: name(...)
        if first_token.type == TokenType.identifier:
            # Parse name to see if it's followed by '('
            self._tokens.pop_position()  # Restore to parse from name
            self._tokens.push_position()  # Save for backtracking

            name = self.name()
            if not name:
                self._tokens.pop_position()
                return None

            # Check if this is a function call
            next_token = self._tokens.peek()
            if next_token and next_token.type == TokenType.bracket_open_round:
                # It's a function call - parse it
                self._tokens.pop_position()  # Pop the push_position
                function_call = self.function_call()
                if not function_call:
                    return None
                return FunctionCallValue(function_call.main_token, function_call)

            # Not a function call, restore position and return name
            self._tokens.pop_position()
            return Name(name.main_token, name.identifier, name.inner)

        # No valid expression found
        self._tokens.pop_position()
        self._add_error(f"Unexpected token {first_token.type} in expression")
        return None

    def undefined_value(self) -> Optional[UndefinedValue]:
        """Parse undefined value"""
        token = self._consume_keyword(self._keyword_undefined_value)

        if token is None:
            return None

        return UndefinedValue(token)

    def name(self) -> Optional[Name]:
        """parse name node"""
        identifier = self.identifier()

        if identifier is None:
            return None

        # Проверяем, есть ли следующий токен и является ли он точкой
        next_token = self._tokens.peek()
        if next_token is not None and next_token.type == TokenType.operator_dot:
            self._tokens.next()  # consume '.'
            inner = self.name()

            if inner is None:
                return None
        else:
            inner = None

        return Name(identifier.main_token, identifier, inner)

    def function_call_value(self) -> Optional[FunctionCallValue]:
        """parse function call"""
        function_call = self.function_call()

        if function_call is None:
            return None

        return FunctionCallValue(function_call.main_token, function_call)

    def address_take(self) -> Optional[AddressTake]:
        """parse address take"""
        token = self._consume(TokenType.operator_address)

        if token is None:
            return None

        name = self.name()

        if name is None:
            return None

        return AddressTake(token, name)

    def integer_literal(self) -> Optional[IntegerLiteral]:
        """parse integer literal"""
        token = self._consume_set({
            TokenType.literal_int_bin,
            TokenType.literal_int_hex,
            TokenType.literal_int_dec,
            TokenType.literal_int_char,
        })

        if token is None:
            return None

        return IntegerLiteral(token, token.value)

    def real_literal(self) -> Optional[RealLiteral]:
        """parse real literal"""
        token = self._consume_set({
            TokenType.literal_real,
            TokenType.literal_real_exp,
        })

        if token is None:
            return None

        return RealLiteral(token, token.value)

    def string_literal(self) -> Optional[StringLiteral]:
        """parse string literal"""
        token = self._consume(TokenType.literal_string)

        if token is None:
            return None

        return StringLiteral(token, token.value)

    def list_literal(self) -> Optional[ListLiteral]:
        """parse list literal"""
        first = self._tokens.peek()
        values = self._parse_brackets_figure(self.expression)

        if values is None:
            return None

        return ListLiteral(first, values)

    def statement(self) -> Optional[Statement]:
        """Dispatch statement parsing based on first token"""
        # Save position for all statement attempts
        self._tokens.push_position()

        # Check first token to determine statement type
        first_token = self._tokens.peek()
        if not first_token:
            self._tokens.pop_position()
            self._add_error("Unexpected EOF in statement")
            return None

        # Local symbol statement: def ...
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_symbol_define:
            self._tokens.pop_position()
            return self.local_symbol_statement()

        # Local variable statement: var ...
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_variable:
            self._tokens.pop_position()
            return self.local_variable_statement()

        # Return statement: return ...
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_return:
            self._tokens.pop_position()
            return self.return_statement()

        # Try assign or function call statement (both start with name)
        if first_token.type == TokenType.identifier:
            # Parse name to see what follows
            self._tokens.pop_position()  # Restore to parse from name
            self._tokens.push_position()  # Save for backtracking

            name = self.name()
            if not name:
                self._tokens.pop_position()
                return None

            # Check next token after name
            next_token = self._tokens.peek()
            if not next_token:
                self._tokens.pop_position()
                self._add_error("Unexpected EOF after name in statement")
                return None

            # Assign statement: name = ...
            if next_token.type == TokenType.operator_assign:
                self._tokens.pop_position()
                return self.assign_statement()

            # Function call statement: name(...)
            if next_token.type == TokenType.bracket_open_round:
                self._tokens.pop_position()
                return self.function_call_statement()

            # Neither assign nor function call - error
            self._tokens.pop_position()
            self._add_error("Expected '=' or '(' after name in statement")
            return None

        # No valid statement found
        self._tokens.pop_position()
        self._add_error(f"Unexpected token {first_token.type} in statement")
        return None

    def local_symbol_statement(self) -> Optional[LocalSymbol]:
        """parse local symbol"""
        symbol = self.symbol()

        if symbol is None:
            return None

        return LocalSymbol(symbol.main_token, symbol)

    def local_variable_statement(self) -> Optional[LocalVariable]:
        """parse local variable"""
        variable = self.variable()

        if variable is None:
            return None

        return LocalVariable(variable.main_token, variable)

    def assign_statement(self) -> Optional[Assign]:
        """parse assign"""
        name = self.name()

        if name is None:
            return None

        if self._consume(TokenType.operator_assign) is None:
            return None

        expression = self.expression()

        if expression is None:
            return None

        return Assign(name.main_token, name, expression)

    def function_call_statement(self) -> Optional[FunctionCallStatement]:
        """parse function call"""
        function_call = self.function_call()

        if function_call is None:
            return None

        return FunctionCallStatement(function_call.main_token, function_call)

    def return_statement(self) -> Optional[Return]:
        """parse return statement"""

        token = self._consume_keyword(self._keyword_return)

        if token is None:
            return None

        # Проверяем, есть ли следующий токен
        next_token = self._tokens.peek()

        if next_token is None or next_token.type == TokenType.newline:
            expression = None

        else:
            expression = self.expression()

            if expression is None:
                return None

        return Return(token, expression)

    def type(self) -> Optional[Type]:
        """Dispatch type parsing based on first token"""
        # Save position for all type attempts
        self._tokens.push_position()

        # Check first token to determine type category
        first_token = self._tokens.peek()
        if not first_token:
            self._tokens.pop_position()
            return None

        # Pointer type: *T
        if first_token.type == TokenType.operator_star:
            self._tokens.pop_position()
            return self.pointer_type()

        # Array or slice type: [size]T or []T
        if first_token.type == TokenType.bracket_open_square:
            self._tokens.pop_position()
            # Сохраняем позицию для отката
            self._tokens.push_position()

            # Потребляем '['
            if self._consume(TokenType.bracket_open_square) is None:
                self._tokens.pop_position()
                return None

            # Проверяем, что следует за '['
            next_token = self._tokens.peek()

            if next_token and next_token.type == TokenType.bracket_close_square:
                # Это срез
                self._tokens.next()  # Потребляем ']'
                _type = self.type()
                if _type is None:
                    self._tokens.pop_position()
                    return None
                self._tokens.pop_position()
                return SliceType(first_token, _type)
            else:
                # Это должен быть массив
                size = self.integer_literal()
                if size is None:
                    self._tokens.pop_position()
                    # Если это не срез и не массив, то ошибка
                    self._add_error("Expected integer literal or ']' after '['")
                    return None

                if self._consume(TokenType.bracket_close_square) is None:
                    self._tokens.pop_position()
                    return None

                _type = self.type()
                if _type is None:
                    self._tokens.pop_position()
                    return None

                self._tokens.pop_position()
                return ArrayType(first_token, size, _type)

        # Function type with body: fn (...) T { ... }
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_function:
            self._tokens.pop_position()
            return self.function_type()

        # Struct type: struct { ... }
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_struct:
            self._tokens.pop_position()
            return self.struct_type()

        # Function signature type: (...) T
        if first_token.type == TokenType.bracket_open_round:
            self._tokens.pop_position()
            return self.function_signature_type()

        # Pure type (named type): name
        self._tokens.pop_position()
        return self.pure_type()

    def pointer_type(self) -> Optional[PointerType]:
        """parse pointer type"""
        token = self._consume(TokenType.operator_star)

        if token is None:
            return None

        _type = self.type()

        if _type is None:
            return None

        return PointerType(token, _type)

    def array_type(self) -> Optional[ArrayType]:
        """parse array type"""
        token = self._consume(TokenType.bracket_open_square)

        if token is None:
            return None

        size = self.integer_literal()

        if size is None:
            return None

        if self._consume(TokenType.bracket_close_square) is None:
            return None

        _type = self.type()

        if _type is None:
            return None

        return ArrayType(token, size, _type)

    def slice_type(self) -> Optional[SliceType]:
        """parse slice type"""
        token = self._consume(TokenType.bracket_open_square)

        if token is None:
            return None

        if self._consume(TokenType.bracket_close_square) is None:
            return None

        _type = self.type()

        if _type is None:
            return None

        return SliceType(token, _type)

    def function_signature_type(self) -> Optional[FunctionSignatureType]:
        """parse function signature type"""
        function_signature = self.function_signature()

        if function_signature is None:
            return None

        return FunctionSignatureType(function_signature.main_token, function_signature)

    def pure_type(self) -> Optional[PureType]:
        """parse pure type"""
        name = self.name()

        if name is None:
            return None

        return PureType(name.main_token, name)

    def struct_type(self) -> Optional[StructType]:
        """parse struct type"""
        token = self._consume_keyword(self._keyword_struct)

        if token is None:
            return None

        if self._consume(TokenType.bracket_open_figure) is None:
            return None

        module = self.module()

        if module is None:
            return None

        if self._consume(TokenType.bracket_close_figure) is None:
            return None

        return StructType(token, module)

    def function_type(self) -> Optional[FunctionType]:
        """parse function type"""
        token = self._consume_keyword(self._keyword_function)

        if token is None:
            return None

        function_signature_type = self.function_signature_type()

        if function_signature_type is None:
            return None

        if self._consume(TokenType.bracket_open_figure) is None:
            return None

        statements = list[Statement]()

        while True:
            token = self._tokens.peek()  # Используем peek

            if token is None:
                self._add_error("Unexpected EOF in function type")
                return None

            if token.type == TokenType.bracket_close_figure:
                self._tokens.next()  # Потребляем закрывающую скобку
                break

            if token.type == TokenType.newline:
                self._tokens.next()
                continue

            statement = self.statement()

            if statement is None:
                return None

            statements.append(statement)

        return FunctionType(token, function_signature_type, statements)

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

    def _consume_set(self, expected_types: set[TokenType]) -> Optional[Token]:
        """
        Eat token of expected type or none and write error
        :param expected_types:
        :return: Token with expected type or None
        """
        token = self._tokens.next()

        if token is None:
            self._add_error(f"Expected any in {expected_types}, got EOF")
            return None

        if token.type not in expected_types:
            self._add_error(f"Expected any in {expected_types}, got {token.type}")
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
            ignore: Optional[TokenType] = None
    ) -> Optional[Sequence[T]]:
        """Parse list of items separated by delimiter, terminated by terminator."""

        def _skip():
            while ignore and self._tokens.peek() and self._tokens.peek().type == ignore:
                self._tokens.next()

        _skip()

        if self._tokens.peek() and self._tokens.peek().type == terminator:
            self._tokens.next()
            return ()

        items = list[T]()

        while True:
            item = element_parser()

            if item is None:
                return None if not items else None

            items.append(item)
            _skip()

            if self._tokens.peek() and self._tokens.peek().type == terminator:
                self._tokens.next()
                return items

            if not self._tokens.peek() or self._tokens.peek().type != delimiter:
                return None

            self._tokens.next()
            _skip()

            if self._tokens.peek() and self._tokens.peek().type == terminator:
                self._tokens.next()
                return items

    def _parse_brackets[T](
            self,
            element_parser: Callable[[], Optional[T]],
            first: TokenType,
            last: TokenType,
    ) -> Optional[Sequence[T]]:
        if self._consume(first) is None:
            return None

        return self._parse_list(element_parser, TokenType.delimiter_comma, last, TokenType.newline)

    def _parse_brackets_round[T](self, element_parser: Callable[[], Optional[T]]) -> Optional[Sequence[T]]:
        return self._parse_brackets(element_parser, TokenType.bracket_open_round, TokenType.bracket_close_round)

    def _parse_brackets_figure[T](self, element_parser: Callable[[], Optional[T]]) -> Optional[Sequence[T]]:
        return self._parse_brackets(element_parser, TokenType.bracket_open_figure, TokenType.bracket_close_figure)
