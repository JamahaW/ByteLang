from __future__ import annotations

import struct
from typing import Final


class Type:
    """Примитивный тип данных"""

    POINTER_CHAR = "*"

    def __init__(self, name: str, _format: str, _id: int, signed: bool):
        if not name:
            raise ValueError(f"Name Must be set (not {name})")

        self.name: Final[str] = name

        if _id <= 0:
            raise ValueError(f"TypeID Must be > 0 (got {_id}")

        self.id: Final[int] = _id

        if _format not in 'c?bBhHiIqQfd':
            raise ValueError(f'Invalid format: {_format}')

        self.format = _format
        self.signed = signed

        self.__packer = struct.Struct(self.format)
        self.size = self.__packer.size

        self.min = -signed * 2 ** (8 * self.size - 1)
        self.max = 2 ** (8 * self.size - int(signed)) - 1

    def __repr__(self):
        return f"Primitive({self.name})@{self.id}({self.size}) -> {self.format} [{self.min}; {self.max}]"

    def __str__(self):
        return self.name

    def toBytes(self, value: int) -> bytes:
        return self.__packer.pack(value)


class Collection:
    """Набор примитивных типов"""

    BOOL = Type("bool", '?', 0x1, False)
    INT8 = Type("i8", 'b', 0x2, True)
    UINT8 = Type("u8", 'B', 0x3, False)
    INT16 = Type('i16', 'h', 0x4, True)
    UINT16 = Type('u16', 'H', 0x5, False)
    INT32 = Type('i32', 'i', 0x6, True)
    UINT32 = Type('u32', 'I', 0x7, False)
    INT64 = Type('i64', 'q', 0x8, True)
    UINT64 = Type('u64', 'Q', 0x9, False)
    FLOAT32 = Type('f32', 'f', 0xA, True)
    FLOAT64 = Type('f64', 'd', 0xB, True)

    PRIMITIVES = {"char": None, "bool": BOOL, "i8": INT8, "u8": UINT8, "i16": INT16, "u16": UINT16, "i32": INT32, "u32": UINT32, "i64": INT64, "u64": UINT64, "f32": FLOAT32, "f64": FLOAT64}

    @classmethod
    def get(cls, typename: str) -> Type:
        """Получить экземпляр примитивного типа по идентификатору"""
        return cls.PRIMITIVES.get(typename)

    @classmethod
    def pointer(cls, width: int) -> Type:
        return cls.PRIMITIVES.get(f"u{width * 8}")
