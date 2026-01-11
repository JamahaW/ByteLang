from pathlib import Path

from miz import Lexer, Parser


def test_parser(path: Path):
    with open(path, encoding="utf-8") as f:
        source_code = f.read()

    lexer = Lexer(path.name, source_code)
    tokens = lexer.tokenize()

    if lexer.errors():
        print("Lexer errors:")
        for error in lexer.errors():
            print(f"  {error}")
        return

    if not tokens:
        print("No tokens generated")
        return

    parser = Parser(tokens)
    ast = parser.module()

    if ast is not None:
        print(f"{ast}")
    else:
        print('\n'.join((f"{i:4}: {t.type}({t.value})" for i, t in enumerate(tokens))))
        print('\n'.join(map(str, parser.errors())))


if __name__ == "__main__":
    test_parser(Path("feature.miz"))
