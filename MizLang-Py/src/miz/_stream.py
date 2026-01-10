# Copyright 2026 KiraFlux
# SPDX-License-Identifier: Apache-2.0

"""
Streams
"""

from typing import Final, Optional, Sequence


class OutputStream[T]:
    """
    Output Stream with position tracking
    """

    def __init__(self, items: Sequence[T]) -> None:
        self._items: Final = items
        self._position = 0
        self._position_stack: Final[list[int]] = []

    def push_position(self) -> None:
        """Push current position onto stack"""
        self._position_stack.append(self._position)

    def pop_position(self) -> None:
        """Pop position from stack and restore it"""
        self._position = self._position_stack.pop()

    def peek(self) -> Optional[T]:
        """Get current item without consuming it"""
        if self._position < len(self._items):
            return self._items[self._position]
        return None

    def next(self) -> Optional[T]:
        """Consume and return current item"""
        item = self.peek()
        if item is not None:
            self._position += 1
        return item

    def is_eof(self) -> bool:
        """Check if end of stream reached"""
        return self._position >= len(self._items)
