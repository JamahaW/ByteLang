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
from bytelang._ast import Break
from bytelang._ast import Condition
from bytelang._ast import Continue
from bytelang._ast import Declaration
from bytelang._ast import Expression
from bytelang._ast import Field
from bytelang._ast import FunctionCall
from bytelang._ast import FunctionSignature
from bytelang._ast import FunctionType
from bytelang._ast import Identifier
from bytelang._ast import IntegerLiteral
from bytelang._ast import ListLiteral
from bytelang._ast import Loop
from bytelang._ast import Name
from bytelang._ast import Public
from bytelang._ast import RealLiteral
from bytelang._ast import Return
from bytelang._ast import SliceType
from bytelang._ast import StarOperator
from bytelang._ast import Statement
from bytelang._ast import StatementsBlock
from bytelang._ast import StringLiteral
from bytelang._ast import StructType
from bytelang._ast import Symbol
from bytelang._ast import UndefinedValue
from bytelang._ast import Variable
from bytelang._stream import OutputStream
from bytelang._token import Token
from bytelang._token import TokenType


class Parser:
    """ByteLang parser"""

    @dataclass(frozen=True)
    class Error:
        """Parsing Error"""
        message: str
        token: Optional[Token]

    # Keywords
    _keyword_public: ClassVar = "pub"
    _keyword_variable: ClassVar = "var"
    _keyword_symbol_define: ClassVar = "def"
    _keyword_undefined_value: ClassVar = "undefined"
    _keyword_function: ClassVar = "fn"
    _keyword_return: ClassVar = "return"
    _keyword_struct: ClassVar = "struct"
    _keyword_if: ClassVar = "if"
    _keyword_else: ClassVar = "else"
    _keyword_loop: ClassVar = "loop"
    _keyword_break: ClassVar = "break"
    _keyword_continue: ClassVar = "continue"

    def __init__(self, tokens: Sequence[Token]) -> None:
        self._tokens: Final = OutputStream(tokens)
        self._errors: Final = list[Parser.Error]()

    def errors(self) -> Sequence[Error]:
        """Get possible errors"""
        return self._errors

    # Basic parsing methods

    def identifier(self) -> Optional[Identifier]:
        """Parse identifier"""
        token: Optional[Token[str]] = self._consume(TokenType.identifier)

        if token is None:
            return None

        return Identifier(main_token=token, id=token.value)

    def name(self) -> Optional[Name]:
        """Parse name (identifier with optional dots)"""
        identifier = self.identifier()

        if identifier is None:
            return None

        # Check for dot operator for nested names
        next_token = self._tokens.peek()
        if next_token and next_token.type == TokenType.operator_dot:
            self._tokens.next()  # Consume '.'
            inner = self.name()

            if inner is None:
                return None

            return Name(main_token=identifier.main_token, identifier=identifier, inner=inner)

        return Name(main_token=identifier.main_token, identifier=identifier, inner=None)

    # Expression parsing

    def expression(self) -> Optional[Expression]:
        """Parse expression"""
        # Skip leading newlines
        while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
            self._tokens.next()

        first_token = self._tokens.peek()

        if not first_token:
            self._add_error("Unexpected EOF in expression")
            return None

        # Address take: &name
        if first_token.type == TokenType.operator_address:
            return self._parse_address_take()

        # Undefined value
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_undefined_value:
            return self._parse_undefined_value()

        # Integer literals
        if first_token.type in {
            TokenType.literal_int_bin,
            TokenType.literal_int_hex,
            TokenType.literal_int_dec,
            TokenType.literal_int_char,
        }:
            return self._parse_integer_literal()

        # Real literals
        if first_token.type in {TokenType.literal_real, TokenType.literal_real_exp}:
            return self._parse_real_literal()

        # String literal
        if first_token.type == TokenType.literal_string:
            return self._parse_string_literal()

        # List literal
        if first_token.type == TokenType.bracket_open_figure:
            return self._parse_list_literal()

        # Star operator: *expression
        if first_token.type == TokenType.operator_star:
            return self._parse_star_operator()

        # Array or slice type: [size]expression or []expression
        if first_token.type == TokenType.bracket_open_square:
            return self._parse_array_or_slice_type()

        # Function signature: (args) return_type
        if first_token.type == TokenType.bracket_open_round:
            return self._parse_function_signature()

        # Function type: fn (...) { ... }
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_function:
            return self._parse_function_type()

        # Struct type: struct { ... }
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_struct:
            return self._parse_struct_type()

        # Identifier (could be name or function call)
        if first_token.type == TokenType.identifier:
            return self._parse_name_or_function_call()

        # No valid expression
        self._add_error(f"Unexpected token {first_token.type} in expression")
        return None

    def _parse_address_take(self) -> Optional[AddressTake]:
        """Parse &name"""
        token = self._consume(TokenType.operator_address)
        if token is None:
            return None

        name = self.name()
        if name is None:
            return None

        return AddressTake(main_token=token, name=name)

    def _parse_undefined_value(self) -> Optional[UndefinedValue]:
        """Parse undefined"""
        token = self._consume_keyword(self._keyword_undefined_value)
        if token is None:
            return None
        return UndefinedValue(main_token=token)

    def _parse_integer_literal(self) -> Optional[IntegerLiteral]:
        """Parse integer literal"""
        token = self._consume_set({
            TokenType.literal_int_bin,
            TokenType.literal_int_hex,
            TokenType.literal_int_dec,
            TokenType.literal_int_char,
        })
        if token is None:
            return None
        return IntegerLiteral(main_token=token, value=token.value)

    def _parse_real_literal(self) -> Optional[RealLiteral]:
        """Parse real literal"""
        token = self._consume_set({TokenType.literal_real, TokenType.literal_real_exp})
        if token is None:
            return None
        return RealLiteral(main_token=token, value=token.value)

    def _parse_string_literal(self) -> Optional[StringLiteral]:
        """Parse string literal"""
        token = self._consume(TokenType.literal_string)
        if token is None:
            return None
        return StringLiteral(main_token=token, value=token.value)

    def _parse_list_literal(self) -> Optional[ListLiteral]:
        """Parse list literal"""
        token = self._tokens.peek()
        values = self._parse_brackets_figure(self.expression)
        if values is None:
            return None
        return ListLiteral(main_token=token, values=values)

    def _parse_star_operator(self) -> Optional[StarOperator]:
        """Parse *expression"""
        token = self._consume(TokenType.operator_star)
        if token is None:
            return None

        target = self.expression()
        if target is None:
            return None

        return StarOperator(main_token=token, type=target)

    def _parse_array_or_slice_type(self) -> Optional[ArrayType | SliceType]:
        """Parse [size]expression or []expression"""
        open_token = self._consume(TokenType.bracket_open_square)
        if open_token is None:
            return None

        # Check if it's a slice (empty brackets)
        next_token = self._tokens.peek()
        if next_token and next_token.type == TokenType.bracket_close_square:
            self._tokens.next()  # Consume ']'
            item_type = self.expression()
            if item_type is None:
                return None
            return SliceType(main_token=open_token, item_type=item_type)

        # It's an array - parse size
        size = self.expression()
        if size is None:
            self._add_error("Expected integer literal for array size")
            return None

        if self._consume(TokenType.bracket_close_square) is None:
            return None

        item_type = self.expression()
        if item_type is None:
            return None

        return ArrayType(main_token=open_token, size=size, item_type=item_type)

    def _parse_function_signature(self) -> Optional[FunctionSignature]:
        """Parse (arguments) return_type"""
        open_token = self._tokens.peek()
        arguments = self._parse_brackets_round(self._parse_field)

        if arguments is None:
            return None

        return_type = self.expression()
        if return_type is None:
            return None

        return FunctionSignature(main_token=open_token, arguments=arguments, return_type=return_type)

    def _parse_function_type(self) -> Optional[FunctionType]:
        """Parse fn (arguments) return_type { statements }"""
        token = self._consume_keyword(self._keyword_function)
        if token is None:
            return None

        signature = self._parse_function_signature()
        if signature is None:
            return None

        body = self._parse_statements_block()
        if body is None:
            return None

        return FunctionType(token, signature, body)

    def _parse_struct_type(self) -> Optional[StructType]:
        """Parse struct { declarations }"""
        struct_token = self._consume_keyword(self._keyword_struct)
        if struct_token is None:
            return None

        # Пропускаем newlines перед {
        while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
            self._tokens.next()

        if self._consume(TokenType.bracket_open_figure) is None:
            return None

        declarations = self._parse_declarations_block(TokenType.bracket_close_figure, allow_commas=True)
        if declarations is None:
            return None

        # Пропускаем newlines перед }
        while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
            self._tokens.next()

        if self._consume(TokenType.bracket_close_figure) is None:
            return None

        return StructType(main_token=struct_token, declarations=declarations)

    def _parse_name_or_function_call(self) -> Optional[Expression]:
        """Parse name or function call"""
        # Save position for backtracking
        self._tokens.push_position()

        # Parse name first
        name = self.name()
        if name is None:
            self._tokens.pop_position()
            return None

        # Check if it's followed by '(' - function call
        next_token = self._tokens.peek()
        if next_token and next_token.type == TokenType.bracket_open_round:
            # Don't restore position - we're sure it's a function call
            self._tokens.pop_position()  # Remove saved position
            # Now parse from the beginning of name again
            self._tokens.push_position()  # Save current position
            self._tokens.pop_position()  # Restore to position before name

            # Parse name again
            name = self.name()
            arguments = self._parse_brackets_round(self.expression)
            if arguments is None:
                return None
            return FunctionCall(main_token=name.main_token, name=name, arguments=arguments)

        # Just a name - restore to position before name parsing
        self._tokens.pop_position()

        # Parse name without looking ahead
        name = self.name()
        if name is None:
            return None

        return name

    # Statement parsing

    def statement(self) -> Optional[Statement]:
        """Parse statement"""
        # Skip leading newlines
        while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
            self._tokens.next()

        first_token = self._tokens.peek()

        if not first_token:
            self._add_error("Unexpected EOF in statement")
            return None

        # Symbol definition: def name = expression
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_symbol_define:
            return self._parse_symbol()

        # Variable declaration: var field = expression
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_variable:
            return self._parse_variable()

        # Return statement: return [expression]
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_return:
            return self._parse_return_statement()

        # break
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_break:
            return self._parse_break_statement()

        # continue
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_continue:
            return self._parse_continue_statement()

        # loop
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_loop:
            return self._parse_loop_statement()

        # if
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_if:
            return self._parse_condition_statement()

        # Try to parse as name (could be assignment or function call)
        if first_token.type == TokenType.identifier:
            # Save position for backtracking
            self._tokens.push_position()

            name = self.name()
            if name is None:
                self._tokens.pop_position()
                return None

            # Check next token
            next_token = self._tokens.peek()
            if not next_token:
                self._tokens.pop_position()
                self._add_error("Unexpected EOF after name")
                return None

            # Assignment: name = expression
            if next_token.type == TokenType.operator_assign:
                self._tokens.pop_position()  # Restore to beginning of name
                # Now parse the assignment
                name = self.name()  # Parse name again
                self._tokens.next()  # Consume '='
                expression = self.expression()
                if expression is None:
                    return None
                return Assign(main_token=name.main_token, name=name, expression=expression)

            # Function call: name(arguments)
            if next_token.type == TokenType.bracket_open_round:
                self._tokens.pop_position()  # Restore to beginning of name
                # Parse as function call
                name = self.name()  # Parse name again
                arguments = self._parse_brackets_round(self.expression)
                if arguments is None:
                    return None
                return FunctionCall(main_token=name.main_token, name=name, arguments=arguments)

            # Neither - error
            self._tokens.pop_position()
            self._add_error("Expected '=' or '(' after name")
            return None

        # No valid statement
        self._add_error(f"Unexpected token {first_token.type} in statement")
        return None

    def _parse_symbol(self) -> Optional[Symbol]:
        """Parse def name = expression"""
        def_token = self._consume_keyword(self._keyword_symbol_define)
        if def_token is None:
            return None

        identifier = self.identifier()
        if identifier is None:
            return None

        if self._consume(TokenType.operator_assign) is None:
            return None

        expression = self.expression()
        if expression is None:
            return None

        return Symbol(main_token=def_token, identifier=identifier, expression=expression)

    def _parse_variable(self) -> Optional[Variable]:
        """Parse var field = expression"""
        var_token = self._consume_keyword(self._keyword_variable)
        if var_token is None:
            return None

        field = self._parse_field()
        if field is None:
            return None

        if self._consume(TokenType.operator_assign) is None:
            return None

        expression = self.expression()
        if expression is None:
            return None

        return Variable(main_token=var_token, field=field, expression=expression)

    def _parse_return_statement(self) -> Optional[Return]:
        """Parse return [expression]"""
        return_token = self._consume_keyword(self._keyword_return)
        if return_token is None:
            return None

        # Skip newlines after return
        while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
            self._tokens.next()

        # Check if there's an expression or just return
        next_token = self._tokens.peek()
        if next_token is None:
            return Return(main_token=return_token, returns=None)

        # If next token is newline or closing brace, it's empty return
        if next_token.type == TokenType.newline or next_token.type == TokenType.bracket_close_figure:
            return Return(main_token=return_token, returns=None)

        # Try to parse expression
        expression = self.expression()
        if expression is None:
            # Couldn't parse expression, but might still be valid empty return
            # Check if next token is newline or closing brace
            next_after_error = self._tokens.peek()
            if next_after_error and (next_after_error.type == TokenType.newline or
                                     next_after_error.type == TokenType.bracket_close_figure):
                return Return(main_token=return_token, returns=None)
            return None

        return Return(main_token=return_token, returns=expression)

    def _parse_break_statement(self) -> Optional[Break]:
        """parse break"""
        token = self._consume_keyword(self._keyword_break)

        if token is None:
            return None

        return Break(token)

    def _parse_continue_statement(self) -> Optional[Continue]:
        """parse break"""
        token = self._consume_keyword(self._keyword_continue)

        if token is None:
            return None

        return Continue(token)

    def _parse_loop_statement(self) -> Optional[Loop]:
        """parse break"""
        token = self._consume_keyword(self._keyword_loop)

        if token is None:
            return None

        body = self._parse_statements_block()
        if body is None:
            return None

        return Loop(token, body)

    def _parse_condition_statement(self) -> Optional[Condition]:
        """parse break"""
        if_token = self._consume_keyword(self._keyword_if)

        if if_token is None:
            return None

        condition = self.expression()

        if condition is None:
            return None

        then_body = self._parse_statements_block()

        if then_body is None:
            return None

        else_token = self._tokens.peek()

        if else_token is not None and else_token.type == TokenType.identifier and else_token.value == self._keyword_else:
            self._tokens.next()

            else_body = self._parse_statements_block()

            if else_token is None:
                return None

        else:
            else_body = StatementsBlock(if_token, ())

        return Condition(if_token, condition, then_body, else_body)

    # Declaration parsing

    def declaration(self) -> Optional[Declaration]:
        """Parse declaration"""
        # Skip leading newlines
        while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
            self._tokens.next()

        first_token = self._tokens.peek()

        if not first_token:
            return None

        # Public declaration: pub declaration
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_public:
            return self._parse_public_declaration()

        # Symbol definition: def name = expression
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_symbol_define:
            return self._parse_symbol()

        # Variable declaration: var field = expression
        if first_token.type == TokenType.identifier and first_token.value == self._keyword_variable:
            return self._parse_variable()

        # Field declaration: name: expression
        if first_token.type == TokenType.identifier:
            return self._parse_field()

        # No valid declaration
        self._add_error(f"Unexpected token {first_token.type} in declaration")
        return None

    def _parse_public_declaration(self) -> Optional[Public]:
        """Parse pub declaration"""
        pub_token = self._consume_keyword(self._keyword_public)
        if pub_token is None:
            return None

        declaration = self.declaration()
        if declaration is None:
            return None

        return Public(main_token=pub_token, inner=declaration)

    def _parse_field(self) -> Optional[Field]:
        """Parse name: expression"""
        identifier = self.identifier()
        if identifier is None:
            return None

        if self._consume(TokenType.delimiter_colon) is None:
            return None

        field_type = self.expression()
        if field_type is None:
            return None

        return Field(main_token=identifier.main_token, identifier=identifier, type=field_type)

    # Block parsing

    def _parse_statements_block(self) -> Optional[StatementsBlock]:
        """ '{' <stmt>* '}' """

        def __block() -> Optional[Sequence[Statement]]:
            ret = list[Statement]()

            while True:
                # Skip newlines
                while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
                    self._tokens.next()

                # Check for end of block
                t = self._tokens.peek()

                if not t:
                    break

                if t.type == TokenType.bracket_close_figure:
                    break

                # Parse statement
                s = self.statement()
                if s is None:
                    # Couldn't parse statement, but might be end of block
                    # Check if next token is closing brace
                    if self._tokens.peek() and self._tokens.peek().type == TokenType.bracket_close_figure:
                        break
                    return None

                ret.append(s)

            return ret

        # Пропускаем newlines перед телом функции
        while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
            self._tokens.next()

        token = self._consume(TokenType.bracket_open_figure)
        if token is None:
            return None

        statements = __block()
        if statements is None:
            return None

        # Пропускаем newlines перед закрывающей скобкой
        while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
            self._tokens.next()

        if self._consume(TokenType.bracket_close_figure) is None:
            return None

        return StatementsBlock(token, statements)

    def _parse_declarations_block(self, terminator: Optional[TokenType] = None, allow_commas: bool = False) -> Optional[Sequence[Declaration]]:
        """Parse block of declarations with optional commas"""
        declarations = list[Declaration]()

        while True:
            # Skip newlines
            while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
                self._tokens.next()

            # Check for terminator or EOF
            token = self._tokens.peek()
            if not token:
                break
            if terminator and token.type == terminator:
                break

            # Parse declaration
            declaration = self.declaration()
            if declaration is None:
                # Couldn't parse declaration, check if it's terminator
                if terminator and self._tokens.peek() and self._tokens.peek().type == terminator:
                    break
                return None

            declarations.append(declaration)

            # Skip newlines
            while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
                self._tokens.next()

            # Check for comma or terminator
            next_token = self._tokens.peek()
            if not next_token:
                break

            if terminator and next_token.type == terminator:
                continue

            if allow_commas and next_token.type == TokenType.delimiter_comma:
                self._tokens.next()  # Consume comma
                continue

            # If no terminator (parsing module), just continue to next declaration
            if not terminator:
                continue

            # If allow_commas is True, but we didn't get a comma or terminator, it's an error
            if allow_commas:
                self._add_error(f"Expected comma or '{terminator}', got {next_token.type}")
                return None

        return declarations

    # Module parsing

    def module(self) -> Optional[StructType]:
        """Parse module (file) as a struct type"""
        # Skip initial newlines
        while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
            self._tokens.next()

        first_token = self._tokens.peek()
        if not first_token:
            # Empty module
            from bytelang._token import SourcePosition
            dummy_token = Token(
                token_type=TokenType.identifier,
                value="module",
                source_position=SourcePosition("", 0, 1, 1)
            )
            return StructType(main_token=dummy_token, declarations=())

        declarations = self._parse_declarations_block(None, allow_commas=False)
        if declarations is None:
            return None

        return StructType(main_token=first_token, declarations=declarations)

    # Helper methods for parsing lists

    def _parse_brackets_round[T](self, element_parser: Callable[[], Optional[T]]) -> Optional[Sequence[T]]:
        """Parse (element, element, ...)"""
        if self._consume(TokenType.bracket_open_round) is None:
            return None

        # Empty brackets
        if self._tokens.peek() and self._tokens.peek().type == TokenType.bracket_close_round:
            self._tokens.next()
            return ()

        elements = list[T]()

        while True:
            # Skip newlines
            while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
                self._tokens.next()

            # Parse element
            element = element_parser()
            if element is None:
                return None

            elements.append(element)

            # Skip newlines
            while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
                self._tokens.next()

            # Check for comma or closing bracket
            next_token = self._tokens.peek()
            if not next_token:
                self._add_error("Unexpected EOF in brackets")
                return None

            if next_token.type == TokenType.bracket_close_round:
                self._tokens.next()
                return elements

            if next_token.type == TokenType.delimiter_comma:
                self._tokens.next()
                continue

            self._add_error(f"Expected comma or ')', got {next_token.type}")
            return None

    def _parse_brackets_figure[T](self, element_parser: Callable[[], Optional[T]]) -> Optional[Sequence[T]]:
        """Parse {element, element, ...}"""
        if self._consume(TokenType.bracket_open_figure) is None:
            return None

        # Empty brackets
        if self._tokens.peek() and self._tokens.peek().type == TokenType.bracket_close_figure:
            self._tokens.next()
            return ()

        elements = list[T]()

        while True:
            # Skip newlines
            while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
                self._tokens.next()

            # Parse element
            element = element_parser()
            if element is None:
                return None

            elements.append(element)

            # Skip newlines
            while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
                self._tokens.next()

            # Check for comma or closing bracket
            next_token = self._tokens.peek()
            if not next_token:
                self._add_error("Unexpected EOF in braces")
                return None

            if next_token.type == TokenType.bracket_close_figure:
                self._tokens.next()
                return elements

            if next_token.type == TokenType.delimiter_comma:
                self._tokens.next()
                continue

            self._add_error(f"Expected comma or '}}', got {next_token.type}")
            return None

    # Token consumption helpers

    def _add_error(self, message: str) -> None:
        """Add parsing error"""
        self._errors.append(self.Error(message, self._tokens.peek()))

    def _consume(self, expected_type: TokenType) -> Optional[Token]:
        """Consume token of expected type or add error"""
        token = self._tokens.next()

        if token is None:
            self._add_error(f"Expected {expected_type}, got EOF")
            return None

        if token.type != expected_type:
            self._add_error(f"Expected {expected_type}, got {token.type}")
            return None

        return token

    def _consume_set(self, expected_types: set[TokenType]) -> Optional[Token]:
        """Consume token of any expected type or add error"""
        token = self._tokens.next()

        if token is None:
            self._add_error(f"Expected any of {expected_types}, got EOF")
            return None

        if token.type not in expected_types:
            self._add_error(f"Expected any of {expected_types}, got {token.type}")
            return None

        return token

    def _consume_keyword(self, expected_identifier: str) -> Optional[Token]:
        """Consume identifier token with expected value"""
        token = self._consume(TokenType.identifier)

        if token is None:
            return None

        if token.value != expected_identifier:
            self._add_error(f"Expected keyword '{expected_identifier}', got '{token.value}'")
            return None

        return token
