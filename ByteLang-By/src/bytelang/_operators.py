from enum import StrEnum


class UnaryOp(StrEnum):
    """Unary operators"""
    positive = "+"
    negative = "-"
    star = "*"
    address_of = "&"
    logical_not = "not"


class BinaryOp(StrEnum):
    """Binary operators"""
    # type cast
    type_cast = "as"

    # Arithmetic
    add = "+"
    sub = "-"
    mul = "*"
    div = "/"
    mod = "%"

    # Bitwise
    bitwise_and = "&"
    bitwise_or = "|"
    bitwise_xor = "^"
    shift_left = "<<"
    shift_right = ">>"

    # Comparison
    equal = "=="
    not_equal = "!="
    less = "<"
    greater = ">"
    less_equal = "<="
    greater_equal = ">="

    # Logical
    logical_and = "and"
    logical_or = "or"
