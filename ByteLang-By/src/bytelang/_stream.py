from typing import Final
from typing import Optional
from typing import Sequence


class OutputStream[T]:
    """
    Output Stream
    """

    def __init__(self, items: Sequence[T]) -> None:
        self._items: Final = items
        self._position = 0
        self._position_stack = list[int]()

    def push_position(self) -> None:
        """Push actual position in stack"""
        self._position_stack.append(self._position)

    def pop_position(self) -> None:
        """Pop current position from stack"""
        self._position = self._position_stack.pop()

    def peek(self) -> Optional[T]:
        """Get item on cursor if available"""
        if not self.is_eof():
            return self._items[self._position]

        return None

    def next(self) -> Optional[T]:
        """Increment position and peek"""
        ret = self.peek()
        self._position += 1
        return ret

    def is_eof(self) -> bool:
        """Check if we're at end of stream"""
        return self._position >= len(self._items)
