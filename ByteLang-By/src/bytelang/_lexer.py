from dataclasses import dataclass
from typing import Final
from typing import Optional
from typing import Sequence
from typing import final

from bytelang._token import SourcePosition
from bytelang._token import Token
from bytelang._token import TokenType


@final
class Lexer:
    """Simple ByteLang Lexer"""

    @final
    @dataclass(frozen=True, kw_only=True)
    class Error:
        """Lexer error"""

        message: str
        source_position: SourcePosition

        def __str__(self):
            return f"{self.source_position} - error: {self.message}"

    def __init__(self, source_name: str, source_code: str) -> None:
        self._source_code = source_code
        self._source_position = SourcePosition(source_name, 0, 1, 1)
        self._tokens: Final = list[Token]()
        self._errors: Final = list[Lexer.Error]()

    def tokens(self) -> Optional[Sequence[Token]]:
        """Available tokens"""
        if self._errors:
            return None

        return self._tokens

    def errors(self) -> Sequence[Error]:
        """Available errors"""
        return self._errors

    def process(self) -> None:
        """Convert source to tokens"""
        while self._source_position.cursor < len(self._source_code):
            matched = False

            for token_type in TokenType:
                match = token_type.pattern.match(self._source_code, self._source_position.cursor)

                if match is None:
                    continue

                lexeme = match.group(0)

                if not token_type.skip():
                    self._add_token(lexeme, token_type)

                self._source_position.cursor = match.end()
                self._source_position.col += len(lexeme)

                if token_type == TokenType.newline:
                    self._source_position.new_line()

                matched = True
                break

            if not matched:
                char = self._source_code[self._source_position.cursor]
                self._add_error(f"Unexpected character {char}")

                self._source_position.cursor += 1
                self._source_position.col += 1

    def _add_token(self, lexeme: str, token_type: TokenType):
        self._tokens.append(token_type.make(lexeme, self._source_position.clone()))

    def _add_error(self, message: str):
        self._errors.append(self.Error(
            message=message,
            source_position=self._source_position.clone()
        ))
