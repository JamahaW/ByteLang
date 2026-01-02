from bytelang import IdentifierNode
from bytelang import Lexer
from bytelang import Parser

_source_1 = """my_id"""


def _lexer_run(name: str, source: str):
    lexer = Lexer(name, source)
    lexer.process()
    tokens = lexer.tokens()

    if tokens is None:
        print('\n'.join(map(str, lexer.errors())))
        return

    print('\n'.join(map(str, tokens)))

    parser = Parser(tokens)

    node = IdentifierNode.parse(parser)
    print(node)
    print('parser errors:', '\n'.join(map(str, parser.errors())))

    return


_lexer_run("<string>", _source_1)
