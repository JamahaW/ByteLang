from typing import Final

from bytelang._token import Token
from bytelang._token import TokenType


class Lexer:
    """Simple lexer for ByteLang"""

    def __init__(self, keywords: set[str]) -> None:
        self._keywords: Final = keywords

    def lex(self, source: str) -> list[Token]:
        """Convert source to tokens"""

        position = 0
        line = 1
        col = 1
        tokens = list[Token]()

        while position < len(source):
            matched = False

            for token_type in TokenType:
                match = token_type.pattern.match(source, position)

                if match is not None:
                    lexeme = match.group(0)

                    token = token_type.make(lexeme, line, col)

                    if not token_type.skip():
                        # Check if identifier is a keyword
                        if token_type == TokenType.identifier and token.value in self._keywords:
                            token.type = TokenType.keyword

                        tokens.append(token)

                    # Update position
                    position = match.end()
                    col += len(lexeme)

                    # Handle newlines
                    if token_type == TokenType.newline:
                        line += 1
                        col = 1

                    matched = True
                    break

            if not matched:
                # Unexpected character
                char = source[position]
                raise SyntaxError(f"Unexpected character '{char}' at line {line}, col {col}")

        return tokens


# Пример использования
if __name__ == "__main__":
    # Пример кода ByteLang
    __test_code = """
//!math.bl
pub fn add(ret: *i16, a: *i16, b: *i16) void = 0x00

//!sketch.bl
import math

var x: i16 = 20
var result: i16

fn calculate(a: i16, b: i16) i16 {
    var sum: i16
    math.add(sum, a, b)
    return sum
}

pub fn main() void {
    result = calculate(100, x)
}
"""

    # Ключевые слова языка
    KEYWORDS = {
        'import', 'pub', 'const', 'var', 'fn', 'struct',
        'type', 'macro',
    }

    __lexer = Lexer(KEYWORDS)
    __tokens = __lexer.lex(__test_code)

    # Вывод токенов
    for __token in __tokens:
        print(f"{__token.type.name:20} {repr(__token.value):20} line={__token.line:3} col={__token.col:3}")
