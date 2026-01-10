# Copyright 2026 KiraFlux
# SPDX-License-Identifier: Apache-2.0

"""
MizLang
AST
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

from miz._operators import BinaryOp, UnaryOp
from miz._token import Token


@dataclass(frozen=True)
class Node:
    """
    Base AST node
    """

    token: Token = field(repr=False)


@dataclass(frozen=True)
class Expression(Node):
    """
    Expression node (evaluates to a value)
    <expr>
    """


@dataclass(frozen=True)
class Statement(Node):
    """
    Statement node (performs an action)
    <stmt>
    """


@dataclass(frozen=True)
class Declaration(Node):
    """
    <decl>
    """


@dataclass(frozen=True)
class Identifier(Expression):
    """
    <id>
    """

    name: str


@dataclass(frozen=True)
class IntegerLiteral(Expression):
    """
    <literal-integer>
    """

    value: int


@dataclass(frozen=True)
class RealLiteral(Expression):
    """
    <literal-real>
    """

    value: float


@dataclass(frozen=True)
class StringLiteral(Expression):
    """
    <literal-string>
    """

    value: str


@dataclass(frozen=True)
class ListLiteral(Expression):
    """
    <literal-list> :: '{' <expr>* '}'
    """

    values: Sequence[Expression]


@dataclass(frozen=True)
class UndefinedLiteral(Expression):
    """
    <literal-undefined>
    """


@dataclass(frozen=True)
class UnaryExpression(Expression):
    """
    <unary-op> :: 'unary-op' <expr>
    """

    operator: UnaryOp
    operand: Expression


@dataclass(frozen=True)
class BinaryExpression(Expression):
    """
    <binary-op> :: <expr> 'binary-op' <expr>
    """

    operator: BinaryOp
    left: Expression
    right: Expression


@dataclass(frozen=True)
class CallExpression(Expression, Statement):
    """
    <call> :: <expr> '(' <expr>* ')'
    """

    callee: Expression
    arguments: Sequence[Expression]


@dataclass(frozen=True)
class IndexExpression(Expression):
    """
    <get-item> :: <expr> '[' <expr> ']'
    """

    container: Expression
    index: Expression


@dataclass(frozen=True)
class MemberExpression(Expression):
    """
    <get-member> :: <expr> '.' <id>
    """

    object: Expression
    member: Identifier


@dataclass(frozen=True)
class Field(Declaration):
    """
    <field> :: <name> ':' <expr>
    """

    name: Identifier
    type: Expression


@dataclass(frozen=True)
class FunctionSignature(Expression):
    """
    <sig> :: 'sig' '(' <expr>* ')' <expr>
    """

    parameters_types: Sequence[Expression]
    return_type: Expression


@dataclass(frozen=True)
class FunctionType(Expression):
    """
    <fn> :: 'fn' '(' <field>* ')' <expr> <block>
    """

    parameters: Sequence[Field]
    return_type: Expression
    body: Block


@dataclass(frozen=True)
class ArrayType(Expression):
    """
    <array> :: '[' <expr> ']' <expr>
    """

    size: Expression
    element_type: Expression


@dataclass(frozen=True)
class SliceType(Expression):
    """
    <array> :: '[' ']' <expr>
    """

    element_type: Expression


@dataclass(frozen=True)
class StructType(Expression):
    """
    <struct> :: 'struct' '{' <decl>* '}'
    """

    declarations: Sequence[Declaration]


@dataclass(frozen=True)
class Block(Statement):
    """
    <block> :: '{' <stmt>* '}'
    """

    statements: Sequence[Statement]


@dataclass(frozen=True)
class IfStatement(Statement):
    """
    <if> :: 'if' <expr> <block> ['else' <block>]
    """

    condition: Expression
    then_branch: Block
    else_branch: Optional[Block]


@dataclass(frozen=True)
class LoopStatement(Statement):
    """
    <loop> :: <block>
    """
    body: Block


@dataclass(frozen=True)
class ReturnStatement(Statement):
    """
    <return> :: 'return' [<expr>]
    """
    value: Optional[Expression]


@dataclass(frozen=True)
class BreakStatement(Statement):
    """
    <break> :: 'break'
    """


@dataclass(frozen=True)
class ContinueStatement(Statement):
    """
    <continue> :: 'continue>
    """


@dataclass(frozen=True)
class AssignStatement(Statement):
    """
    <assign> :: <expr> '=' <expr>
    """

    target: Expression
    value: Expression


@dataclass(frozen=True)
class Public(Declaration):
    """
    <public> :: 'pub' <decl>
    """

    declaration: Declaration


@dataclass(frozen=True)
class Symbol(Declaration, Statement):
    """
    <symbol> :: 'def' <id> '=' <expr>
    """

    name: Identifier
    value: Expression


@dataclass(frozen=True)
class Variable(Declaration, Statement):
    """
    <variable> :: 'var' <field> '=' <expr>
    """

    field: Field
    value: Expression
