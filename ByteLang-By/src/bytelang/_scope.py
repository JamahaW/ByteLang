from enum import IntEnum
from enum import auto


class ScopeType(IntEnum):
    """Scope"""

    module = auto()
    """Only module"""

    function = auto()
    """Only function body"""

    struct = auto()
    """Only inside struct"""
