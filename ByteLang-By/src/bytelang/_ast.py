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
class Symbol(Node):
    """
    Symbol

    'def' <id> '=' <expr>
    """

    identifier: Identifier
    expression: Expression


@dataclass(frozen=True)
class Variable(Node):
    """
    Variable

    'var' <field> '=' <expr>
    """

    field: Field
    expression: Expression


@dataclass(frozen=True)
class Field(Node):
    """
    Field

    <id> ':' <type>
    """

    identifier: Identifier
    type: Type


@dataclass(frozen=True)
class Declaration(Node):
    """
    Declaration
    """


@dataclass(frozen=True)
class PublicDeclaration(Declaration):
    """
    Marks inner declaration as public

    'pub' <declaration>
    """

    inner: Declaration


@dataclass(frozen=True)
class SymbolDeclaration(Declaration):
    """
    Declaration of symbol

    <symbol>
    """

    symbol: Symbol


@dataclass(frozen=True)
class VariableDeclaration(Declaration):
    """
    Declaration of variable

    <variable>
    """

    variable: Variable


@dataclass(frozen=True)
class FieldDeclaration(Declaration):
    """
    Declaration of field

    <field>
    """

    field: Field


@dataclass(frozen=True)
class Module(Node):
    """
    Module

    [<declaration> '\n']*
    """

    declarations: Sequence[Declaration]


@dataclass(frozen=True)
class FunctionCall(Node):
    """
    Function call

    <name> '(' [<expr> [ ',' <expr> ]* ] ')'
    """

    name: Name
    arguments: Sequence[Expression]


@dataclass(frozen=True)
class FunctionSignature(Node):
    """
    Function Signature

    '(' <field> [',' <field>]* ')' <type>
    """
    arguments: Sequence[Field]
    return_type: Type


@dataclass(frozen=True)
class Expression(Node):
    """
    Evaluable Expression
    """


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
class FunctionCallValue(Expression):
    """
    function call as value

    <call>
    """
    function_call: FunctionCall


@dataclass(frozen=True)
class AddressTake(Expression):
    """
    Address of variable

    '&' <name>
    """
    name: Name


@dataclass(frozen=True)
class Dereference(Expression):
    """
    Value of Address

    '*' <name>
    """
    address: Expression


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
class Statement(Node):
    """
    Statement (in function)
    """


@dataclass(frozen=True)
class LocalSymbol(Statement):
    """
    Define local symbol

    <symbol>
    """
    symbol: Symbol


@dataclass(frozen=True)
class LocalVariable(Statement):
    """
    Define local variable

    <variable>
    """
    variable: Variable


@dataclass(frozen=True)
class Assign(Statement):
    """
    Execute assignment

    <name> '=' <expr>
    """
    name: Name
    expression: Expression


@dataclass(frozen=True)
class FunctionCallStatement(Statement):
    """
    Execute function

    <call>
    """
    function_call: FunctionCall


@dataclass(frozen=True)
class Return(Statement):
    """
    Return Statement

    'return [<expr>]'
    """
    returns: Optional[Expression]


@dataclass(frozen=True)
class Type(Expression):
    """
    Type node
    """


@dataclass(frozen=True)
class PointerType(Type):
    """
    Pointer on type

    '*' <type>
    """

    type: Type


@dataclass(frozen=True)
class ArrayType(Type):
    """
    Array

    '[' <integer_literal> ']' <type>
    """

    size: IntegerLiteral
    type: Type


@dataclass(frozen=True)
class SliceType(Type):
    """
    Slice

    `'[' ']' <type>`
    """

    type: Type


@dataclass(frozen=True)
class FunctionSignatureType(Type):
    """
    function signature

    <function_signature>
    """

    function_signature: FunctionSignature


@dataclass(frozen=True)
class PureType(Type):
    """
    Pure type (resolve by name)

    <name>
    """

    name: Name


@dataclass(frozen=True)
class StructType(Type):
    """
    Struct itself

    'struct' '{' <module> '}'
    """

    module: Module


@dataclass(frozen=True)
class FunctionType(Type):
    """
    Function itself

    'fn' <function_signature_type> '{' [<statement> '\n']* '}'
    """

    function_signature_type: FunctionSignatureType
    statements: Sequence[Statement]
