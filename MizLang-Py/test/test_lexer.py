from typing import Optional
from typing import Sequence

from miz import Lexer
from miz import Token

_source_1 = """0b1010"""


def _lexer_run(name: str, source: str):
    lexer = Lexer(name, source)
    lexer.process()
    tokens: Optional[Sequence[Token]] = lexer.tokens()

    if tokens is None:
        print('\n'.join(map(str, lexer.errors())))
        return

    for __token in tokens:
        print(__token)

    return


_lexer_run("test", _source_1)
