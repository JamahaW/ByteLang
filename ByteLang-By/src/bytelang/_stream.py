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

    def peek(self) -> Optional[T]:
        """Get item on cursor if available"""
        if self._position < len(self._items):
            return self._items[self._position]

        return None

    def next(self) -> Optional[T]:
        """Increment position and peek"""
        ret = self.peek()
        self._position += 1
        return ret
