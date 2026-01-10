# Copyright 2026 KiraFlux
# SPDX-License-Identifier: Apache-2.0

"""
Lexical Analyzer
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from typing import Optional
from typing import Sequence

from miz._token import SourcePosition
from miz._token import Token
from miz._token import TokenType


@dataclass(frozen=True)
class LexerError:
    """Lexer error with position"""
    message: str
    source_position: SourcePosition

    def __str__(self):
        return f"{self.source_position}: {self.message}"


class Lexer:
    """Simple lexer for MizLang"""

    def __init__(self, source_name: str, source_code: str) -> None:
        self._source_code = source_code
        self._position = SourcePosition(source_name, 0, 1, 1)
        self._tokens: Final[list[Token]] = []
        self._errors: Final[list[LexerError]] = []

    def tokenize(self) -> Optional[Sequence[Token]]:
        """Tokenize source code, return tokens or None if errors"""
        self._process()
        return self._tokens if not self._errors else None

    def errors(self) -> Sequence[LexerError]:
        """Get lexer errors"""
        return self._errors

    def _process(self) -> None:
        """Main tokenization loop"""
        while self._position.cursor < len(self._source_code):
            matched = False

            for token_type in TokenType:
                match = token_type.pattern.match(self._source_code, self._position.cursor)

                if match is None:
                    continue

                lexeme = match.group(0)

                # Add token if not skipped
                if not token_type.skip():
                    self._add_token(lexeme, token_type)

                # Update position
                self._position.cursor = match.end()

                # Update line and column
                if token_type == TokenType.newline:
                    self._position.new_line()
                else:
                    # Count newlines in lexeme for accurate column tracking
                    lines = lexeme.count('\n')
                    if lines > 0:
                        self._position.line += lines
                        # Column after newlines
                        last_newline = lexeme.rfind('\n')
                        self._position.col = len(lexeme) - last_newline
                    else:
                        self._position.col += len(lexeme)

                matched = True
                break

            # No pattern matched - error
            if not matched:
                char = self._source_code[self._position.cursor]
                self._add_error(f"Unexpected character '{char}'")
                self._position.cursor += 1
                self._position.col += 1

    def _add_token(self, lexeme: str, token_type: TokenType) -> None:
        """Add token to list"""
        self._tokens.append(token_type.make(lexeme, self._position.clone()))

    def _add_error(self, message: str) -> None:
        """Add error to list"""
        self._errors.append(LexerError(message, self._position.clone()))
