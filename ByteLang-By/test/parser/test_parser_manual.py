from bytelang import Lexer
from bytelang import Parser


def test_parser():
    source_code = """
    def math = import()
    """

    lexer = Lexer("test.bl", source_code)
    lexer.process()

    if lexer.errors():
        print("Lexer errors:")
        for error in lexer.errors():
            print(f"  {error}")
        return

    tokens = lexer.tokens()
    if not tokens:
        print("No tokens generated")
        return

    parser = Parser(tokens)
    ast = parser.module()

    if ast is not None:
        print(f"{ast=}")
    else:
        print('\n'.join((f"{i:4}: {t.type}({t.value})" for i, t in enumerate(tokens))))
        print('\n'.join(map(str, parser.errors())))


if __name__ == "__main__":
    test_parser()
