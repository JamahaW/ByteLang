# Copyright 2026 KiraFlux
# SPDX-License-Identifier: Apache-2.0

"""
Defined operators
"""
from enum import Enum, auto


class UnaryOp(Enum):
    """Unary operators"""
    positive = auto()
    negative = auto()
    star = auto()
    address_of = auto()
    logical_not = auto()


class BinaryOp(Enum):
    """Binary operators"""
    # type cast
    type_cast = auto()

    # Arithmetic
    add = auto()
    sub = auto()
    mul = auto()
    div = auto()
    mod = auto()

    # Bitwise
    bitwise_and = auto()
    bitwise_or = auto()
    bitwise_xor = auto()
    shift_left = auto()
    shift_right = auto()

    # Comparison
    equal = auto()
    not_equal = auto()
    less = auto()
    greater = auto()
    less_equal = auto()
    greater_equal = auto()

    # Logical
    logical_and = auto()
    logical_or = auto()
