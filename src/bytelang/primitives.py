from __future__ import annotations

import struct
from typing import Final


# TODO enum
class PrimitiveType:
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
        return f"Primitive({self.name})@{self.size} -> {self.format} [{self.min}; {self.max}]"

    def __str__(self):
        return self.name

    def write(self, value: int | float) -> bytes:
        return self.__packer.pack(value)

    def read(self, buffer: bytes) -> float | str | int:
        return self.__packer.unpack(buffer)[0]

    def readFrom(self, buffer: bytes, index: int) -> float | int | str:
        return self.__packer.unpack_from(buffer, index)[0]

    def writeTo(self, buffer: bytes, index: int, value: int | float | str) -> None:
        self.__packer.pack_into(buffer, index, value)


class PrimitiveCollection:
    """Набор примитивных типов"""

    BOOL = PrimitiveType("bool", '?', 0x1, False)
    INT8 = PrimitiveType("i8", 'b', 0x2, True)
    UINT8 = PrimitiveType("u8", 'B', 0x3, False)
    INT16 = PrimitiveType('i16', 'h', 0x4, True)
    UINT16 = PrimitiveType('u16', 'H', 0x5, False)
    INT32 = PrimitiveType('i32', 'i', 0x6, True)
    UINT32 = PrimitiveType('u32', 'I', 0x7, False)
    INT64 = PrimitiveType('i64', 'q', 0x8, True)
    UINT64 = PrimitiveType('u64', 'Q', 0x9, False)
    FLOAT32 = PrimitiveType('f32', 'f', 0xA, True)
    FLOAT64 = PrimitiveType('f64', 'd', 0xB, True)

    PRIMITIVES_NAME = {"char": None, "bool": BOOL, "i8": INT8, "u8": UINT8, "i16": INT16, "u16": UINT16, "i32": INT32, "u32": UINT32, "i64": INT64, "u64": UINT64, "f32": FLOAT32, "f64": FLOAT64}

    PRIMITIVES_ID = {
        1: BOOL,
        2: INT8,
        3: UINT8,
        4: INT16,
        5: UINT16,
        6: INT32,
        7: UINT32,
        8: INT64,
        9: UINT64,
        10: FLOAT32,
        11: FLOAT64
    }

    @classmethod
    def get(cls, typename: str) -> PrimitiveType:
        """Получить экземпляр примитивного типа по идентификатору"""
        return cls.PRIMITIVES_NAME.get(typename)

    @classmethod
    def pointer(cls, width: int) -> PrimitiveType:
        return cls.PRIMITIVES_NAME.get(f"u{width * 8}")
