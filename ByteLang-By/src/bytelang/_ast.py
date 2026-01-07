from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Optional
from typing import Sequence

from bytelang._token import Token


@dataclass(frozen=True)
class Node:
    """ByteLang AST Node"""

    main_token: Token = field(repr=False)


@dataclass(frozen=True)
class Identifier(Node):
    """
    Pure id

    id_name_123
    """

    id: str


@dataclass(frozen=True)
class Declaration(Node):
    """
    Declaration (in struct)
    """


@dataclass(frozen=True)
class Statement(Node):
    """
    Statement (in function)
    """


@dataclass(frozen=True)
class Expression(Node):
    """
    Evaluable Expression
    """


@dataclass(frozen=True)
class Public(Declaration):
    """
    Marks inner declaration as public

    'pub' <declaration>
    """

    inner: Declaration


@dataclass(frozen=True)
class Field(Declaration):
    """
    Field

    <id> ':' <type>
    """

    identifier: Identifier
    type: Expression


@dataclass(frozen=True)
class Symbol(Declaration, Statement):
    """
    Symbol

    'def' <id> '=' <expr>
    """

    identifier: Identifier
    expression: Expression


@dataclass(frozen=True)
class Variable(Declaration, Statement):
    """
    Variable

    'var' <field> '=' <expr>
    """

    field: Field
    expression: Expression


@dataclass(frozen=True)
class Assign(Statement):
    """
    Execute assignment

    <name> '=' <expr>
    """
    name: Name
    expression: Expression


@dataclass(frozen=True)
class Return(Statement):
    """
    Return Statement

    'return [<expr>]'
    """
    returns: Optional[Expression]


@dataclass(frozen=True)
class FunctionSignature(Expression):
    """
    Function Signature

    '(' <field> [',' <field>]* ')' <type>
    """
    arguments: Sequence[Field]
    return_type: Expression


@dataclass(frozen=True)
class FunctionCall(Statement, Expression):
    """
    Function call

    <name> '(' [<expr> [ ',' <expr> ]* ] ')'
    """

    name: Name
    arguments: Sequence[Expression]


@dataclass(frozen=True)
class UndefinedValue(Expression):
    """
    Undefined initializer value

    'undefined'
    """


@dataclass(frozen=True)
class Name(Expression):
    """
    Name

    <id> ['.' <name>]
    """
    identifier: Identifier
    inner: Optional[Name]


@dataclass(frozen=True)
class AddressTake(Expression):
    """
    Address of variable

    '&' <name>
    """
    name: Name


@dataclass(frozen=True)
class IntegerLiteral(Expression):
    """
    Integer Literal

    <int>
    """
    value: int


@dataclass(frozen=True)
class RealLiteral(Expression):
    """
    real value literal

    <real>
    """
    value: float


@dataclass(frozen=True)
class StringLiteral(Expression):
    """
    String Literal

    <string>
    """
    value: str


@dataclass(frozen=True)
class ListLiteral(Expression):
    """
    Initializer list literal

    '{' <expr> [',' <expr>]* '}'
    """
    values: Sequence[Expression]


@dataclass(frozen=True)
class StarOperator(Expression):
    """
    Pointer on type

    '*' <type>
    """

    type: Expression


@dataclass(frozen=True)
class ArrayType(Expression):
    """
    Array

    '[' <integer_literal> ']' <type>
    """

    size: IntegerLiteral
    item_type: Expression


@dataclass(frozen=True)
class SliceType(Expression):
    """
    Slice

    `'[' ']' <type>`
    """

    item_type: Expression


@dataclass(frozen=True)
class StructType(Expression):
    """Struct type"""

    declarations: Sequence[Declaration]


@dataclass(frozen=True)
class FunctionType(Expression):
    """
    Function itself

    'fn' <function_signature_type> '{' [<statement> '\n']* '}'
    """

    function_signature: FunctionSignature
    statements: Sequence[Statement]
