# Copyright 2026 KiraFlux
# SPDX-License-Identifier: Apache-2.0

"""
MizLang Parser with Pratt parsing
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, ClassVar, Final, Mapping, Optional, Sequence

from miz._ast import (
    ArrayType, AssignStatement, BinaryExpression, Block, BreakStatement, CallExpression, ContinueStatement, Declaration, Expression, Field, FunctionSignature,
    FunctionType, Identifier, IfStatement, IndexExpression, IntegerLiteral, ListLiteral, LoopStatement, MemberExpression, Public, RealLiteral, ReturnStatement,
    SliceType, Statement, StringLiteral, StructType, Symbol, UnaryExpression, UndefinedLiteral, Variable)
from miz._stream import OutputStream
from miz._token import Token, TokenType


@dataclass(frozen=True)
class ParseError:
    """Parsing error with context"""
    message: str
    token: Token

    def __str__(self):
        return f"{self.message}: {self.token}"


class Parser:
    """MizLang parser with Pratt parsing"""

    _binary_op_table: ClassVar = TokenType.build_binary_operator_map()
    _binary_op_precedence_table: ClassVar = TokenType.build_precedence()
    _binary_op_precedence_max: ClassVar = max(_binary_op_precedence_table.values())

    _unary_op_precedence: ClassVar = _binary_op_precedence_max + 1  # Higher than any binary operator
    _unary_op_table: ClassVar = TokenType.build_unary_operator_map()

    def __init__(self, tokens: Sequence[Token]) -> None:
        self._tokens: Final = OutputStream(tokens)
        self._errors: Final = list[ParseError]()

        self._prefix_parsers: Final[Mapping[TokenType, Callable[[Token], Optional[Expression]]]] = {
            # Literals
            TokenType.identifier: self.identifier_expression,
            TokenType.string: self.string_literal,
            TokenType.keyword_undefined: self.undefined_literal,

            # Grouping
            TokenType.paren_open: self.grouped_expression,
            TokenType.brace_open: self.list_literal,
            TokenType.bracket_open: self.array_or_slice,

            # Unary operators
            TokenType.plus: self.unary_operator,
            TokenType.minus: self.unary_operator,
            TokenType.star: self.unary_operator,
            TokenType.ampersand: self.unary_operator,
            TokenType.logical_not: self.unary_operator,

            # Type expressions
            TokenType.keyword_fn: self.function_type,
            TokenType.keyword_sig: self.function_signature,
            TokenType.keyword_struct: self.struct_type,
        }
        """Prefix parser dispatch table"""

        self._infix_parsers: Final[Mapping[TokenType, Callable[[Expression], Optional[Expression]]]] = {
            # Binary operators
            TokenType.plus: self.binary_operator,
            TokenType.minus: self.binary_operator,
            TokenType.star: self.binary_operator,
            TokenType.slash: self.binary_operator,
            TokenType.percent: self.binary_operator,
            TokenType.equal: self.binary_operator,
            TokenType.not_equal: self.binary_operator,
            TokenType.less: self.binary_operator,
            TokenType.greater: self.binary_operator,
            TokenType.less_equal: self.binary_operator,
            TokenType.greater_equal: self.binary_operator,
            TokenType.shift_left: self.binary_operator,
            TokenType.shift_right: self.binary_operator,
            TokenType.ampersand: self.binary_operator,
            TokenType.pipe: self.binary_operator,
            TokenType.caret: self.binary_operator,
            TokenType.logical_and: self.binary_operator,
            TokenType.logical_or: self.binary_operator,
            TokenType.type_cast: self.binary_operator,

            # Postfix operators
            TokenType.dot: self.member_access,
            TokenType.paren_open: self.call_expression,
            TokenType.bracket_open: self.index_expression,
        }
        """Infix parser dispatch table"""

        self._declaration_parsers: Final[Mapping[TokenType, Callable[[], Optional[Declaration]]]] = {
            TokenType.keyword_pub: self.public_declaration,
            TokenType.keyword_def: self.symbol_declaration,
            TokenType.keyword_var: self.variable_declaration,
        }
        """Declaration parser dispatch table"""

        self._statement_parsers: Final[Mapping[TokenType, Callable[[], Optional[Statement]]]] = {
            TokenType.keyword_def: self.symbol_declaration,
            TokenType.keyword_var: self.variable_declaration,
            TokenType.keyword_return: self.return_statement,
            TokenType.keyword_break: self.break_statement,
            TokenType.keyword_continue: self.continue_statement,
            TokenType.keyword_loop: self.loop_statement,
            TokenType.keyword_if: self.if_statement,
        }
        """Statement parser dispatch table"""

    def errors(self) -> Sequence[ParseError]:
        """Get parsing errors"""
        return self._errors

    #  public api

    def module(self) -> Optional[StructType]:
        """Parse entire module/file"""
        self._skip_newlines()

        token = self._tokens.peek()
        if token is None:
            return StructType(Token.dummy(), ())  # Empty module

        declarations = self._parse_declaration_block(None, allow_commas=False)
        if declarations is None:
            return None

        return StructType(token, declarations)

    #  expression parsers

    def expression(self, min_precedence: int = 0) -> Optional[Expression]:
        """Parse expression with Pratt parser"""
        token = self._tokens.peek()
        if not token:
            self._error("Unexpected EOF in expression")
            return None

        # Parse prefix expression
        prefix_parser = self._prefix_parsers.get(token.type)
        if not prefix_parser:
            # Handle literals not in prefix table
            if token.type in TokenType.integer_types():
                left = self.integer_literal()
            elif token.type in TokenType.real_types():
                left = self.real_literal()
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
            if self._binary_op_precedence_table.get(token.type, 0) < min_precedence:
                break

            # Get infix parser for this operator
            infix_parser = self._infix_parsers.get(token.type)
            if not infix_parser:
                break

            left = infix_parser(left)
            if left is None:
                return None

        return left

    def identifier_expression(self, token: Token) -> Optional[Expression]:
        """Parse identifier as expression"""
        # Regular identifier - consume and return
        self._tokens.next()
        return Identifier(token, token.value)

    def unary_operator(self, token: Token) -> Optional[UnaryExpression]:
        """Parse unary operator"""
        # Map token type to operator
        operator = self._unary_op_table.get(token.type)
        if not operator:
            self._error(f"Invalid unary operator: {token.type}")
            return None

        self._tokens.next()  # Consume operator

        # Unary operators have high precedence (right-associative)
        operand = self.expression(self._unary_op_precedence)
        if operand is None:
            return None

        return UnaryExpression(token, operator, operand)

    def binary_operator(self, left: Expression) -> Optional[BinaryExpression]:
        """Parse binary operator"""
        token = self._tokens.peek()
        if not token:
            return None

        # Map token type to operator
        operator = self._binary_op_table.get(token.type)
        if not operator:
            return None

        precedence = self._binary_op_precedence_table.get(token.type, 0)
        self._tokens.next()  # Consume operator

        # For left-associative operators, use precedence + 1
        # For right-associative, use precedence
        # All our binary operators are left-associative
        right = self.expression(precedence + 1)
        if right is None:
            return None

        return BinaryExpression(token, operator, left, right)

    def member_access(self, left: Expression) -> Optional[MemberExpression]:
        """Parse member access: `object.member`"""
        token = self._tokens.next()  # Consume '.'

        identifier = self.identifier()
        if identifier is None:
            self._error("Expected identifier after '.'")
            return None

        return MemberExpression(token, left, identifier)

    def call_expression(self, callee: Expression) -> Optional[CallExpression]:
        """Parse function call: callee(arguments)"""
        open_token = self._tokens.peek()  # Peek '(' but don't consume yet

        self._tokens.push_position()  # Save position in case this is not a call

        arguments = self._parse_comma_separated(TokenType.paren_open, TokenType.paren_close, self.expression)  # Try to parse as function call
        if arguments is None:
            self._tokens.pop_position()  # Not a function call, restore position
            return None

        return CallExpression(open_token, callee, arguments)  # Successfully parsed as function call

    def index_expression(self, container: Expression) -> Optional[IndexExpression]:
        """Parse index access: container[index]"""
        open_token = self._tokens.next()  # Consume '['

        index = self.expression()
        if index is None:
            return None

        if not self._consume(TokenType.bracket_close):
            return None

        return IndexExpression(open_token, container, index)

    def grouped_expression(self, _: Token) -> Optional[Expression]:
        """Parse (expression)"""
        self._tokens.next()  # Consume '('

        expr = self.expression()
        if expr is None:
            return None

        if not self._consume(TokenType.paren_close):
            return None

        return expr

    def array_or_slice(self, token: Token) -> Optional[ArrayType | SliceType]:
        """Parse [size]type or []type"""
        self._tokens.next()  # Consume '['

        # Check for slice []
        if self._tokens.peek() and self._tokens.peek().type == TokenType.bracket_close:
            self._tokens.next()  # Consume ']'
            element_type = self.expression()
            if element_type is None:
                return None
            return SliceType(token, element_type)

        # Array with size [size]type
        size = self.expression()
        if size is None:
            return None

        if not self._consume(TokenType.bracket_close):
            return None

        element_type = self.expression()
        if element_type is None:
            return None

        return ArrayType(token, size, element_type)

    #  literal parsers

    def list_literal(self, token: Token) -> Optional[ListLiteral]:
        """Parse list literal {value, ...}"""
        # Consume `{` in _parse_comma_separated
        values = self._parse_comma_separated(TokenType.brace_open, TokenType.brace_close, self.expression)
        if values is None:
            return None
        return ListLiteral(token, values)

    def identifier(self) -> Optional[Identifier]:
        """Parse identifier"""
        token = self._consume(TokenType.identifier)
        if token is None:
            return None
        return Identifier(token, token.value)

    def integer_literal(self) -> Optional[IntegerLiteral]:
        """Parse integer literal"""
        token = self._consume_set(TokenType.integer_types())
        if token is None:
            return None
        return IntegerLiteral(token, token.value)

    def real_literal(self) -> Optional[RealLiteral]:
        """Parse real literal"""
        token = self._consume_set(TokenType.real_types())
        if token is None:
            return None
        return RealLiteral(token, token.value)

    def string_literal(self, token: Token) -> Optional[StringLiteral]:
        """Parse string literal"""
        self._tokens.next()  # Consume string token
        return StringLiteral(token, token.value)

    #  type parsers

    def undefined_literal(self, token: Token) -> Optional[UndefinedLiteral]:
        """Parse undefined literal"""
        self._tokens.next()  # Consume 'undefined' keyword
        return UndefinedLiteral(token)

    def function_signature(self, token: Token) -> Optional[FunctionSignature]:
        """Parse function signature (params) return_type"""
        self._tokens.next()  # Consume 'sig'

        parameters = self._parse_comma_separated(TokenType.paren_open, TokenType.paren_close, self.expression)
        if parameters is None:
            return None

        return_type = self.expression()
        if return_type is None:
            return None

        return FunctionSignature(token, parameters, return_type)

    def function_type(self, token: Token) -> Optional[FunctionType]:
        """Parse function type"""
        self._tokens.next()  # Consume 'fn'

        parameters = self._parse_comma_separated(TokenType.paren_open, TokenType.paren_close, self.field)
        if parameters is None:
            return None

        return_type = self.expression()
        if return_type is None:
            return None

        body = self.block_statement()
        if body is None:
            return None

        return FunctionType(token, parameters, return_type, body)

    #  statement parsers

    def struct_type(self, token: Token) -> Optional[StructType]:
        """Parse struct type"""
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

    def statement(self) -> Optional[Statement]:
        """Parse a statement"""
        self._skip_newlines()

        token = self._tokens.peek()
        if not token:
            self._error("Unexpected EOF in statement")
            return None

        statement_parser = self._statement_parsers.get(token.type)
        if statement_parser is None:
            return self.expression_statement()  # Expression statements (assignment or function call)
        else:
            return statement_parser()

    def expression_statement(self) -> Optional[Statement]:
        """Parse expression as statement (assignment or call)"""
        expr = self.expression()
        if expr is None:
            return None

        # Check for assignment
        if self._tokens.peek() and self._tokens.peek().type == TokenType.assign:
            self._tokens.next()  # Consume '='
            right = self.expression()

            if right is None:
                return None

            return AssignStatement(expr.token, expr, right)

        # Must be a function call or valid expression statement
        if not isinstance(expr, CallExpression):
            self._error("Expression is not a valid statement")
            return None

        return expr  # CallExpression is both Expression and Statement

    def symbol_declaration(self) -> Optional[Symbol]:
        """Parse symbol declaration: def name = value"""
        token = self._consume(TokenType.keyword_def)
        if token is None:
            return None

        name = self.identifier()
        if name is None:
            return None

        if not self._consume(TokenType.assign):
            return None

        value = self.expression()
        if value is None:
            return None

        return Symbol(token, name, value)

    def variable_declaration(self) -> Optional[Variable]:
        """Parse variable declaration"""
        token = self._consume(TokenType.keyword_var)
        if token is None:
            return None

        field = self.field()
        if field is None:
            return None

        if not self._consume(TokenType.assign):
            return None

        value = self.expression()
        if value is None:
            return None

        return Variable(token, field, value)

    def return_statement(self) -> Optional[ReturnStatement]:
        """Parse return statement"""
        token = self._consume(TokenType.keyword_return)
        if token is None:
            return None

        self._skip_newlines()

        # Check for optional value
        token = self._tokens.peek()
        if not token or token.type in {TokenType.newline, TokenType.brace_close}:
            return ReturnStatement(token, None)

        value = self.expression()
        if value is None:
            return None

        return ReturnStatement(token, value)

    def break_statement(self) -> Optional[BreakStatement]:
        """Parse break statement"""
        token = self._consume(TokenType.keyword_break)
        if token is None:
            return None
        return BreakStatement(token)

    def continue_statement(self) -> Optional[ContinueStatement]:
        """Parse continue statement"""
        token = self._consume(TokenType.keyword_continue)
        if token is None:
            return None
        return ContinueStatement(token)

    def loop_statement(self) -> Optional[LoopStatement]:
        """Parse loop statement"""
        loop_token = self._consume(TokenType.keyword_loop)
        if loop_token is None:
            return None

        body = self.block_statement()
        if body is None:
            return None

        return LoopStatement(loop_token, body)

    #  declaration parsing

    def if_statement(self) -> Optional[IfStatement]:
        """Parse if statement"""
        token = self._consume(TokenType.keyword_if)
        if token is None:
            return None

        condition = self.expression()
        if condition is None:
            return None

        then_branch = self.block_statement()
        if then_branch is None:
            return None

        # Optional else branch
        self._skip_newlines()
        else_branch = None

        if self._tokens.peek() and self._tokens.peek().type == TokenType.keyword_else:
            self._tokens.next()  # Consume 'else'
            else_branch = self.block_statement()
            if else_branch is None:
                return None

        return IfStatement(token, condition, then_branch, else_branch)

    def declaration(self) -> Optional[Declaration]:
        """Parse a declaration"""
        self._skip_newlines()

        token = self._tokens.peek()
        if not token:
            self._error("Expected declaration, got EOF")
            return None

        declaration_parser = self._declaration_parsers.get(token.type)
        if declaration_parser is None:
            return self.field()
        else:
            return declaration_parser()

    def public_declaration(self) -> Optional[Public]:
        """Parse public declaration: pub declaration"""
        token = self._consume(TokenType.keyword_pub)
        if token is None:
            return None

        declaration = self.declaration()
        if declaration is None:
            return None

        return Public(token, declaration)

    #  block parsers

    def field(self) -> Optional[Field]:
        """Parse field declaration: name: type"""
        identifier = self.identifier()
        if identifier is None:
            return None

        if not self._consume(TokenType.colon):
            return None

        type_expr = self.expression()
        if type_expr is None:
            return None

        return Field(identifier.token, identifier, type_expr)

    def block_statement(self) -> Optional[Block]:
        """Parse block of statements"""
        if not self._consume(TokenType.brace_open):
            return None

        statements = list()
        while True:
            self._skip_newlines()

            token = self._tokens.peek()
            if not token or token.type == TokenType.brace_close:
                break

            statement = self.statement()
            if statement is None:
                return None

            statements.append(statement)

        if not self._consume(TokenType.brace_close):
            return None

        return Block(token, statements)

    #  helper methods

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

            declaration = self.declaration()
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

    def _parse_comma_separated[T](self, open_token: TokenType, close_token: TokenType, parser: Callable[[], Optional[T]]) -> Optional[Sequence[T]]:
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
