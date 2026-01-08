from enum import Enum
from enum import StrEnum
from typing import Final


class UnaryOperator(StrEnum):
    """Unary Operators"""

    reference = "&"
    star = "*"
    logical_not = "not"


class BinaryOperator(Enum):
    """Binary Operators"""

    # mul
    mul = ("*", 40)
    div = ("/", 40)
    mod = ("%", 40)

    # additive
    add = ("+", 30)
    sub = ("-", 30)

    # shifts
    bit_shift_left = ("<<", 25)
    bit_shift_right = (">>", 25)

    # bitwise
    bit_and = ("&", 20)
    bit_xor = ("^", 15)
    bit_or = ("|", 10)

    # comparisons
    equal = ("==", 9)
    not_equal = ("!=", 9)
    less = ("<", 9)
    greater = (">", 9)
    less_or_equal = ("<=", 9)
    greater_or_equal = (">=", 9)

    # logical
    logical_and = ("and", 5)
    logical_or = ("or", 4)

    def __init__(self, lexeme: str, priority: int):
        self.lexeme: Final = lexeme
        self.priority: Final = priority
