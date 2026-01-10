# Copyright 2026 KiraFlux
# SPDX-License-Identifier: Apache-2.0

"""
AST
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import Sequence

from miz._operators import BinaryOp
from miz._operators import UnaryOp
from miz._token import Token


@dataclass(frozen=True)
class Node:
    """Base AST node"""
    token: Token = field(repr=False)


@dataclass(frozen=True)
class Expression(Node):
    """Expression node (evaluates to a value)"""


@dataclass(frozen=True)
class Statement(Node):
    """Statement node (performs an action)"""


@dataclass(frozen=True)
class Declaration(Node):
    """Declaration node (defines something)"""


@dataclass(frozen=True)
class Identifier(Expression):
    """Identifier reference"""
    name: str


@dataclass(frozen=True)
class IntegerLiteral(Expression):
    """Integer literal"""
    value: int


@dataclass(frozen=True)
class RealLiteral(Expression):
    """Real number literal"""
    value: float


@dataclass(frozen=True)
class StringLiteral(Expression):
    """String literal"""
    value: str


@dataclass(frozen=True)
class UndefinedLiteral(Expression):
    """Undefined value literal"""


@dataclass(frozen=True)
class UnaryExpression(Expression):
    """Unary operator expression"""
    operator: UnaryOp
    operand: Expression


@dataclass(frozen=True)
class BinaryExpression(Expression):
    """Binary operator expression"""
    operator: BinaryOp
    left: Expression
    right: Expression


@dataclass(frozen=True)
class CallExpression(Expression, Statement):
    """Function call expression (can be both expression and statement)"""
    callee: Expression
    arguments: Sequence[Expression]


@dataclass(frozen=True)
class IndexExpression(Expression):
    """Index access expression"""
    container: Expression
    index: Expression


@dataclass(frozen=True)
class MemberExpression(Expression):
    """Member access expression"""
    object: Expression
    member: Identifier


@dataclass(frozen=True)
class Field(Declaration):
    """Field declaration: name: type"""
    name: Identifier
    type: Expression


@dataclass(frozen=True)
class FunctionSignature(Expression):
    """Function signature: sig (params) return_type"""
    parameters_types: Sequence[Expression]
    return_type: Expression


@dataclass(frozen=True)
class FunctionType(Expression):
    """Function type: fn signature block"""
    parameters: Sequence[Field]
    return_type: Expression
    body: Block


@dataclass(frozen=True)
class ArrayType(Expression):
    """Array type: [size]element_type"""
    size: Expression
    element_type: Expression


@dataclass(frozen=True)
class SliceType(Expression):
    """Slice type: []element_type"""
    element_type: Expression


@dataclass(frozen=True)
class StructType(Expression):
    """Struct type: { declarations }"""
    declarations: Sequence[Declaration]


@dataclass(frozen=True)
class Block(Statement):
    """Block of statements"""
    statements: Sequence[Statement]


@dataclass(frozen=True)
class IfStatement(Statement):
    """If statement: if condition { ... } [else { ... }]"""
    condition: Expression
    then_branch: Block
    else_branch: Optional[Block] = None


@dataclass(frozen=True)
class LoopStatement(Statement):
    """Loop statement: loop { ... }"""
    body: Block


@dataclass(frozen=True)
class ReturnStatement(Statement):
    """Return statement: return [expression]"""
    value: Optional[Expression] = None


@dataclass(frozen=True)
class BreakStatement(Statement):
    """Break statement: break"""


@dataclass(frozen=True)
class ContinueStatement(Statement):
    """Continue statement: continue"""


@dataclass(frozen=True)
class AssignStatement(Statement):
    """Assignment statement: target = value"""
    target: Expression
    value: Expression


@dataclass(frozen=True)
class Public(Declaration):
    """Public declaration: pub declaration"""
    declaration: Declaration


@dataclass(frozen=True)
class Symbol(Declaration, Statement):
    """Symbol declaration: def name = expression"""
    name: Identifier
    value: Expression


@dataclass(frozen=True)
class Variable(Declaration, Statement):
    """Variable declaration: var name: type = value"""
    name: Identifier
    type: Expression
    value: Expression


@dataclass(frozen=True)
class ListLiteral(Expression):
    """List literal: { value, value, ... }"""
    values: Sequence[Expression]
