from typing import Optional, Sequence

from miz import Lexer, Token


def _lexer_run(name: str, source: str):
    lexer = Lexer(name, source)
    tokens: Optional[Sequence[Token]] = lexer.tokenize()

    if tokens is None:
        print('\n'.join(map(str, lexer.errors())))
        return

    for __token in tokens:
        print(__token)

    return


with open("test.miz") as f:
    _lexer_run(f.name, f.read())
