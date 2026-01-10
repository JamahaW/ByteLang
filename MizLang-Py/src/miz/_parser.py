# Copyright 2026 KiraFlux
# SPDX-License-Identifier: Apache-2.0

"""
MizLang Parser with Pratt parsing
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from typing import Final
from typing import Optional
from typing import Sequence

from miz._ast import ArrayType
from miz._ast import AssignStatement
from miz._ast import BinaryExpression
from miz._ast import BinaryOp
from miz._ast import Block
from miz._ast import BreakStatement
from miz._ast import CallExpression
from miz._ast import ContinueStatement
from miz._ast import Declaration
from miz._ast import Expression
from miz._ast import Field
from miz._ast import FunctionSignature
from miz._ast import FunctionType
from miz._ast import Identifier
from miz._ast import IfStatement
from miz._ast import IndexExpression
from miz._ast import IntegerLiteral
from miz._ast import ListLiteral
from miz._ast import LoopStatement
from miz._ast import MemberExpression
from miz._ast import Public
from miz._ast import RealLiteral
from miz._ast import ReturnStatement
from miz._ast import SliceType
from miz._ast import Statement
from miz._ast import StringLiteral
from miz._ast import StructType
from miz._ast import Symbol
from miz._ast import UnaryExpression
from miz._ast import UnaryOp
from miz._ast import UndefinedLiteral
from miz._ast import Variable
from miz._stream import OutputStream
from miz._token import SourcePosition
from miz._token import Token
from miz._token import TokenType


@dataclass(frozen=True)
class ParseError:
    """Parsing error with context"""
    message: str
    token: Optional[Token]

    def __str__(self):
        return f"{self.message}: {self.token}"


class Parser:
    """MizLang parser with Pratt parsing"""

    def __init__(self, tokens: Sequence[Token]) -> None:
        self._tokens = OutputStream(tokens)
        self._errors: Final[list[ParseError]] = list()

        # Precedence table (higher = tighter binding)
        self._precedence = self._build_precedence()
        self._prefix_parsers = self._build_prefix_parsers()
        self._infix_parsers = self._build_infix_parsers()

    def errors(self) -> Sequence[ParseError]:
        """Get parsing errors"""
        return self._errors

    #  public api

    def parse_module(self) -> Optional[StructType]:
        """Parse entire module/file"""
        self._skip_newlines()

        first_token = self._tokens.peek()
        if not first_token:
            # Empty module
            return StructType(
                Token(token_type=TokenType.identifier, value="module",
                      source_position=SourcePosition("", 0, 1, 1)),
                ()
            )

        declarations = self._parse_declaration_block(None, allow_commas=False)
        if declarations is None:
            return None

        return StructType(first_token, declarations)

    def parse_expression(self) -> Optional[Expression]:
        """Parse expression with Pratt parser"""
        return self._parse_expression()

    def parse_statement(self) -> Optional[Statement]:
        """Parse a statement"""
        return self._parse_statement()

    def parse_declaration(self) -> Optional[Declaration]:
        """Parse a declaration"""
        return self._parse_declaration()

    #  pratt parser core

    # todo move to TokenType
    @staticmethod
    def _build_precedence() -> dict[TokenType, int]:
        """Build operator precedence table"""
        return {
            # Logical (lowest)
            TokenType.logical_or: 1,
            TokenType.logical_and: 2,

            # Comparison
            TokenType.equal: 3,
            TokenType.not_equal: 3,
            TokenType.less: 3,
            TokenType.greater: 3,
            TokenType.less_equal: 3,
            TokenType.greater_equal: 3,

            # Bitwise
            TokenType.pipe: 4,
            TokenType.caret: 5,
            TokenType.ampersand: 6,
            TokenType.shift_left: 7,
            TokenType.shift_right: 7,

            # Additive
            TokenType.plus: 8,
            TokenType.minus: 8,

            # Multiplicative
            TokenType.star: 9,
            TokenType.slash: 9,
            TokenType.percent: 9,

            # Postfix
            TokenType.dot: 10,
            TokenType.bracket_open: 10,
            TokenType.paren_open: 10,

            # type cast
            TokenType.type_cast: 11,
        }

    def _build_prefix_parsers(self) -> dict[TokenType, Callable[[Token], Optional[Expression]]]:
        """Build prefix parser dispatch table"""
        return {
            # Literals
            TokenType.identifier: self._parse_identifier_expression,
            TokenType.string: self._parse_string_literal,
            TokenType.keyword_undefined: self._parse_undefined_literal,

            # Grouping
            TokenType.paren_open: self._parse_grouped_expression,
            TokenType.brace_open: self._parse_list_literal,
            TokenType.bracket_open: self._parse_array_or_slice,

            # Unary operators
            TokenType.plus: self._parse_unary_operator,
            TokenType.minus: self._parse_unary_operator,
            TokenType.star: self._parse_unary_operator,
            TokenType.ampersand: self._parse_unary_operator,
            TokenType.logical_not: self._parse_unary_operator,

            # Type expressions
            TokenType.keyword_fn: self._parse_function_type,
            TokenType.keyword_sig: self._parse_function_signature,
            TokenType.keyword_struct: self._parse_struct_type,
        }

    def _build_infix_parsers(self) -> dict[TokenType, Callable[[Expression], Optional[Expression]]]:
        """Build infix parser dispatch table"""
        return {
            # Binary operators
            TokenType.plus: self._parse_binary_operator,
            TokenType.minus: self._parse_binary_operator,
            TokenType.star: self._parse_binary_operator,
            TokenType.slash: self._parse_binary_operator,
            TokenType.percent: self._parse_binary_operator,
            TokenType.equal: self._parse_binary_operator,
            TokenType.not_equal: self._parse_binary_operator,
            TokenType.less: self._parse_binary_operator,
            TokenType.greater: self._parse_binary_operator,
            TokenType.less_equal: self._parse_binary_operator,
            TokenType.greater_equal: self._parse_binary_operator,
            TokenType.shift_left: self._parse_binary_operator,
            TokenType.shift_right: self._parse_binary_operator,
            TokenType.ampersand: self._parse_binary_operator,
            TokenType.pipe: self._parse_binary_operator,
            TokenType.caret: self._parse_binary_operator,
            TokenType.logical_and: self._parse_binary_operator,
            TokenType.logical_or: self._parse_binary_operator,
            TokenType.type_cast: self._parse_binary_operator,

            # Postfix operators
            TokenType.dot: self._parse_member_access,
            TokenType.paren_open: self._parse_call_expression,
            TokenType.bracket_open: self._parse_index_expression,
        }

    def _parse_expression(self, min_precedence: int = 0) -> Optional[Expression]:
        """Pratt parser core"""
        token = self._tokens.peek()
        if not token:
            self._error("Unexpected EOF in expression")
            return None

        # Parse prefix expression
        prefix_parser = self._prefix_parsers.get(token.type)
        if not prefix_parser:
            # Handle literals not in prefix table
            if token.type in TokenType.integer_types():
                left = self._parse_integer_literal()
            elif token.type in TokenType.real_types():
                left = self._parse_real_literal()
            else:
                self._error(f"Unexpected token in expression: {token.type}")
                return None
        else:
            left = prefix_parser(token)

        if left is None:
            return None

        # Parse infix/postfix operators
        while True:
            token = self._tokens.peek()
            if not token:
                break

            # Get precedence of current operator
            precedence = self._get_precedence(token)
            if precedence < min_precedence:
                break

            # Get infix parser for this operator
            infix_parser = self._infix_parsers.get(token.type)
            if not infix_parser:
                break

            left = infix_parser(left)
            if left is None:
                return None

        return left

    #  expression parsers

    def _parse_identifier_expression(self, token: Token) -> Optional[Expression]:
        """Parse identifier as expression"""
        # Regular identifier - consume and return
        self._tokens.next()
        return Identifier(token, token.value)

    def _parse_unary_operator(self, token: Token) -> Optional[UnaryExpression]:
        """Parse unary operator"""
        # Map token type to operator
        op_map = {
            TokenType.plus: UnaryOp.positive,
            TokenType.minus: UnaryOp.negative,
            TokenType.star: UnaryOp.star,
            TokenType.ampersand: UnaryOp.address_of,
            TokenType.logical_not: UnaryOp.logical_not,
        }

        operator = op_map.get(token.type)
        if not operator:
            self._error(f"Invalid unary operator: {token.type}")
            return None

        self._tokens.next()  # Consume operator

        # Unary operators have high precedence (right-associative)
        operand = self._parse_expression(10)  # Higher than any binary operator
        if operand is None:
            return None

        return UnaryExpression(token, operator, operand)

    def _parse_binary_operator(self, left: Expression) -> Optional[BinaryExpression]:
        """Parse binary operator"""
        token = self._tokens.peek()
        if not token:
            return None

        # Map token type to operator
        op_map = {
            TokenType.plus: BinaryOp.add,
            TokenType.minus: BinaryOp.sub,
            TokenType.star: BinaryOp.mul,
            TokenType.slash: BinaryOp.div,
            TokenType.percent: BinaryOp.mod,
            TokenType.ampersand: BinaryOp.bitwise_and,
            TokenType.pipe: BinaryOp.bitwise_or,
            TokenType.caret: BinaryOp.bitwise_xor,
            TokenType.shift_left: BinaryOp.shift_left,
            TokenType.shift_right: BinaryOp.shift_right,
            TokenType.equal: BinaryOp.equal,
            TokenType.not_equal: BinaryOp.not_equal,
            TokenType.less: BinaryOp.less,
            TokenType.greater: BinaryOp.greater,
            TokenType.less_equal: BinaryOp.less_equal,
            TokenType.greater_equal: BinaryOp.greater_equal,
            TokenType.logical_and: BinaryOp.logical_and,
            TokenType.logical_or: BinaryOp.logical_or,
            TokenType.type_cast: BinaryOp.type_cast,
        }

        operator = op_map.get(token.type)
        if not operator:
            return None

        precedence = self._precedence.get(token.type, 0)
        self._tokens.next()  # Consume operator

        # For left-associative operators, use precedence + 1
        # For right-associative, use precedence
        # All our binary operators are left-associative
        right = self._parse_expression(precedence + 1)
        if right is None:
            return None

        return BinaryExpression(token, operator, left, right)

    def _parse_member_access(self, left: Expression) -> Optional[MemberExpression]:
        """Parse member access: object.member"""
        dot_token = self._tokens.next()  # Consume '.'

        identifier = self._parse_identifier()
        if identifier is None:
            self._error("Expected identifier after '.'")
            return None

        return MemberExpression(dot_token, left, identifier)

    def _parse_call_expression(self, callee: Expression) -> Optional[CallExpression]:
        """Parse function call: callee(arguments)"""
        open_token = self._tokens.peek()  # Peek '(' but don't consume yet

        # Save position in case this is not a call
        self._tokens.push_position()

        # Try to parse as function call
        arguments = self._parse_comma_separated(
            TokenType.paren_open,
            TokenType.paren_close,
            self._parse_expression
        )

        if arguments is None:
            # Not a function call, restore position
            self._tokens.pop_position()
            return None

        # Successfully parsed as function call
        return CallExpression(open_token, callee, arguments)

    def _parse_index_expression(self, container: Expression) -> Optional[IndexExpression]:
        """Parse index access: container[index]"""
        open_token = self._tokens.next()  # Consume '['

        index = self._parse_expression()
        if index is None:
            return None

        if not self._consume(TokenType.bracket_close):
            return None

        return IndexExpression(open_token, container, index)

    def _parse_grouped_expression(self, token: Token) -> Optional[Expression]:
        """Parse (expression)"""
        self._tokens.next()  # Consume '('

        expr = self._parse_expression()
        if expr is None:
            return None

        if not self._consume(TokenType.paren_close):
            return None

        return expr

    def _parse_array_or_slice(self, token: Token) -> Optional[ArrayType | SliceType]:
        """Parse [size]type or []type"""
        self._tokens.next()  # Consume '['

        # Check for slice []
        if self._tokens.peek() and self._tokens.peek().type == TokenType.bracket_close:
            self._tokens.next()  # Consume ']'
            element_type = self._parse_expression()
            if element_type is None:
                return None
            return SliceType(token, element_type)

        # Array with size [size]type
        size = self._parse_expression()
        if size is None:
            return None

        if not self._consume(TokenType.bracket_close):
            return None

        element_type = self._parse_expression()
        if element_type is None:
            return None

        return ArrayType(token, size, element_type)

    def _parse_list_literal(self, token: Token) -> Optional[ListLiteral]:
        """Parse list literal {value, ...}"""
        # # Consume '{' in _parse_comma_separated
        values = self._parse_comma_separated(
            TokenType.brace_open,
            TokenType.brace_close,
            self._parse_expression
        )
        if values is None:
            return None
        return ListLiteral(token, values)

    #  literal parsers

    def _parse_identifier(self) -> Optional[Identifier]:
        """Parse identifier"""
        token = self._consume(TokenType.identifier)
        if token is None:
            return None
        return Identifier(token, token.value)

    def _parse_integer_literal(self) -> Optional[IntegerLiteral]:
        """Parse integer literal"""
        token = self._consume_set(TokenType.integer_types())
        if token is None:
            return None
        return IntegerLiteral(token, token.value)

    def _parse_real_literal(self) -> Optional[RealLiteral]:
        """Parse real literal"""
        token = self._consume_set(TokenType.real_types())
        if token is None:
            return None
        return RealLiteral(token, token.value)

    def _parse_string_literal(self, token: Token) -> Optional[StringLiteral]:
        """Parse string literal"""
        self._tokens.next()  # Consume string token
        return StringLiteral(token, token.value)

    def _parse_undefined_literal(self, token: Token) -> Optional[UndefinedLiteral]:
        """Parse undefined literal"""
        self._tokens.next()  # Consume 'undefined' keyword
        return UndefinedLiteral(token)

    #  type parsers

    def _parse_function_signature(self, token: Token) -> Optional[FunctionSignature]:
        """Parse function signature (params) return_type"""
        # token is the 'sig' keyword token
        self._tokens.next()  # Consume 'sig'

        parameters = self._parse_comma_separated(
            TokenType.paren_open,
            TokenType.paren_close,
            self._parse_expression
        )

        if parameters is None:
            return None

        return_type = self._parse_expression()
        if return_type is None:
            return None

        return FunctionSignature(token, parameters, return_type)

    def _parse_function_type(self, token: Token) -> Optional[FunctionType]:
        """Parse function type"""
        # token is the 'fn' keyword token
        self._tokens.next()  # Consume 'fn'

        parameters = self._parse_comma_separated(
            TokenType.paren_open,
            TokenType.paren_close,
            self._parse_field
        )

        if parameters is None:
            return None

        return_type = self._parse_expression()
        if return_type is None:
            return None

        body = self._parse_block()
        if body is None:
            return None

        return FunctionType(token, parameters, return_type, body)

    def _parse_struct_type(self, token: Token) -> Optional[StructType]:
        """Parse struct type"""
        # token is the 'struct' keyword token
        self._tokens.next()  # Consume 'struct'

        self._skip_newlines()
        if not self._consume(TokenType.brace_open):
            return None

        declarations = self._parse_declaration_block(TokenType.brace_close, allow_commas=True)
        if declarations is None:
            return None

        self._skip_newlines()
        if not self._consume(TokenType.brace_close):
            return None

        return StructType(token, declarations)

    #  statement parsers

    def _parse_statement(self) -> Optional[Statement]:
        """Parse a statement"""
        self._skip_newlines()

        token = self._tokens.peek()
        if not token:
            self._error("Unexpected EOF in statement")
            return None

        # Keyword statements
        if token.type == TokenType.keyword_def:
            return self._parse_symbol_declaration()
        if token.type == TokenType.keyword_var:
            return self._parse_variable_declaration()
        if token.type == TokenType.keyword_return:
            return self._parse_return_statement()
        if token.type == TokenType.keyword_break:
            return self._parse_break_statement()
        if token.type == TokenType.keyword_continue:
            return self._parse_continue_statement()
        if token.type == TokenType.keyword_loop:
            return self._parse_loop_statement()
        if token.type == TokenType.keyword_if:
            return self._parse_if_statement()

        # Expression statements (assignment or function call)
        return self._parse_expression_statement()

    def _parse_expression_statement(self) -> Optional[Statement]:
        """Parse expression as statement (assignment or call)"""
        expr = self._parse_expression()
        if expr is None:
            return None

        # Check for assignment
        if self._tokens.peek() and self._tokens.peek().type == TokenType.assign:
            # It's an assignment
            self._tokens.next()  # Consume '='
            right = self._parse_expression()

            if right is None:
                return None

            return AssignStatement(expr.token, expr, right)

        # Must be a function call or valid expression statement
        if not isinstance(expr, CallExpression):
            self._error("Expression is not a valid statement")
            return None

        return expr  # CallExpression is both Expression and Statement

    def _parse_symbol_declaration(self) -> Optional[Symbol]:
        """Parse symbol declaration: def name = value"""
        def_token = self._consume(TokenType.keyword_def)
        if def_token is None:
            return None

        name = self._parse_identifier()
        if name is None:
            return None

        if not self._consume(TokenType.assign):
            return None

        value = self._parse_expression()
        if value is None:
            return None

        return Symbol(def_token, name, value)

    def _parse_variable_declaration(self) -> Optional[Variable]:
        """Parse variable declaration: var name: type = value"""
        var_token = self._consume(TokenType.keyword_var)
        if var_token is None:
            return None

        name = self._parse_identifier()
        if name is None:
            return None

        if not self._consume(TokenType.colon):
            return None

        type_expr = self._parse_expression()
        if type_expr is None:
            return None

        if not self._consume(TokenType.assign):
            return None

        value = self._parse_expression()
        if value is None:
            return None

        return Variable(var_token, name, type_expr, value)

    def _parse_return_statement(self) -> Optional[ReturnStatement]:
        """Parse return statement"""
        return_token = self._consume(TokenType.keyword_return)
        if return_token is None:
            return None

        self._skip_newlines()

        # Check for optional value
        token = self._tokens.peek()
        if not token or token.type in {TokenType.newline, TokenType.brace_close}:
            return ReturnStatement(return_token, None)

        value = self._parse_expression()
        if value is None:
            return None

        return ReturnStatement(return_token, value)

    def _parse_break_statement(self) -> Optional[BreakStatement]:
        """Parse break statement"""
        token = self._consume(TokenType.keyword_break)
        if token is None:
            return None
        return BreakStatement(token)

    def _parse_continue_statement(self) -> Optional[ContinueStatement]:
        """Parse continue statement"""
        token = self._consume(TokenType.keyword_continue)
        if token is None:
            return None
        return ContinueStatement(token)

    def _parse_loop_statement(self) -> Optional[LoopStatement]:
        """Parse loop statement"""
        loop_token = self._consume(TokenType.keyword_loop)
        if loop_token is None:
            return None

        body = self._parse_block()
        if body is None:
            return None

        return LoopStatement(loop_token, body)

    def _parse_if_statement(self) -> Optional[IfStatement]:
        """Parse if statement"""
        if_token = self._consume(TokenType.keyword_if)
        if if_token is None:
            return None

        condition = self._parse_expression()
        if condition is None:
            return None

        then_branch = self._parse_block()
        if then_branch is None:
            return None

        # Optional else branch
        self._skip_newlines()
        else_branch = None

        if self._tokens.peek() and self._tokens.peek().type == TokenType.keyword_else:
            self._tokens.next()  # Consume 'else'
            else_branch = self._parse_block()
            if else_branch is None:
                return None

        return IfStatement(if_token, condition, then_branch, else_branch)

    #  declaration parsing

    def _parse_declaration(self) -> Optional[Declaration]:
        """Parse a declaration"""
        self._skip_newlines()

        token = self._tokens.peek()
        if not token:
            self._error("Expected declaration, got EOF")
            return None

        if token.type == TokenType.keyword_pub:
            return self._parse_public_declaration()

        if token.type == TokenType.keyword_def:
            return self._parse_symbol_declaration()

        if token.type == TokenType.keyword_var:
            return self._parse_variable_declaration()

        # Field declaration (name: type)
        return self._parse_field()

    def _parse_public_declaration(self) -> Optional[Public]:
        """Parse public declaration: pub declaration"""
        pub_token = self._consume(TokenType.keyword_pub)
        if pub_token is None:
            return None

        declaration = self._parse_declaration()
        if declaration is None:
            return None

        return Public(pub_token, declaration)

    def _parse_field(self) -> Optional[Field]:
        """Parse field declaration: name: type"""
        name = self._parse_identifier()
        if name is None:
            return None

        if not self._consume(TokenType.colon):
            return None

        type_expr = self._parse_expression()
        if type_expr is None:
            return None

        return Field(name.token, name, type_expr)

    #  block parsers

    def _parse_block(self) -> Optional[Block]:
        """Parse block of statements"""
        token = self._tokens.peek()

        if not self._consume(TokenType.brace_open):
            return None

        statements = list()
        while True:
            self._skip_newlines()

            token = self._tokens.peek()
            if not token or token.type == TokenType.brace_close:
                break

            stmt = self._parse_statement()
            if stmt is None:
                return None

            statements.append(stmt)

        if not self._consume(TokenType.brace_close):
            return None

        return Block(token, statements)

    def _parse_declaration_block(self, terminator: Optional[TokenType], allow_commas: bool) -> Optional[Sequence[Declaration]]:
        """Parse block of declarations"""
        declarations = list()

        while True:
            self._skip_newlines()

            token = self._tokens.peek()
            if not token:
                break

            if terminator and token.type == terminator:
                break

            declaration = self._parse_declaration()
            if declaration is None:
                if terminator and self._tokens.peek() and self._tokens.peek().type == terminator:
                    break
                return None

            declarations.append(declaration)

            self._skip_newlines()

            # Check for separator
            next_token = self._tokens.peek()
            if not next_token:
                break

            if terminator and next_token.type == terminator:
                continue

            if allow_commas and next_token.type == TokenType.comma:
                self._tokens.next()
                continue

            if not terminator:
                continue

            if allow_commas:
                self._error(f"Expected comma or '{terminator}', got {next_token.type}")
                return None

        return declarations

    #  helper methods

    def _parse_comma_separated[T](self, open_token: TokenType, close_token: TokenType,
                                  parser: Callable[[], Optional[T]]) -> Optional[Sequence[T]]:
        """Parse comma-separated list: (item, item, ...)"""
        if not self._consume(open_token):
            return None

        # Empty list
        if self._tokens.peek() and self._tokens.peek().type == close_token:
            self._tokens.next()
            return ()

        items = list()
        while True:
            self._skip_newlines()

            item = parser()
            if item is None:
                return None

            items.append(item)

            self._skip_newlines()

            # Check for comma or closing token
            token = self._tokens.peek()
            if not token:
                self._error(f"Unexpected EOF, expected '{close_token}'")
                return None

            if token.type == close_token:
                self._tokens.next()
                return items

            if token.type == TokenType.comma:
                self._tokens.next()
                continue

            self._error(f"Expected comma or '{close_token}', got {token.type}")
            return None

    def _get_precedence(self, token: Token) -> int:
        """Get operator precedence"""
        return self._precedence.get(token.type, 0)

    def _skip_newlines(self) -> None:
        """Skip newline tokens"""
        while self._tokens.peek() and self._tokens.peek().type == TokenType.newline:
            self._tokens.next()

    def _consume(self, expected_type: TokenType) -> Optional[Token]:
        """Consume token of expected type"""
        token = self._tokens.next()
        if token is None:
            self._error(f"Expected {expected_type}, got EOF")
            return None
        if token.type != expected_type:
            self._error(f"Expected {expected_type}, got {token.type}")
            return None
        return token

    def _consume_set(self, expected_types: set[TokenType]) -> Optional[Token]:
        """Consume token of any expected type"""
        token = self._tokens.next()
        if token is None:
            self._error(f"Expected any of {expected_types}, got EOF")
            return None
        if token.type not in expected_types:
            self._error(f"Expected any of {expected_types}, got {token.type}")
            return None
        return token

    def _error(self, message: str) -> None:
        """Add parsing error"""
        self._errors.append(ParseError(message, self._tokens.peek()))
