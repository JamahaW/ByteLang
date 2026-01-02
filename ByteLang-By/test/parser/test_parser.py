from bytelang import Lexer
from bytelang import Parser


def test_parser():
    source_code = """
math = import("math.bl")
stack = import("stack.bl")

def MAX_VALUE = 100
var counter: i32 = 0

def add = fn(a: i32, b: i32) i32 {
    var result: i32
    math.add(result, a, b)
    return result
}

def native_add = cast( *fn(*i32, *i32, *i32), 0x67 )

def Point =struct {
    x: i32
    y: i32

    def length = fn(self: *Point) i32 {
        var temp: i32
        math.mul(temp, self.x, self.x)
        var temp2: i32
        math.mul(temp2, self.y, self.y)
        math.add(temp, temp, temp2)
        return temp
    }
}
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
    ast = parser.run()

    print(ast)


if __name__ == "__main__":
    test_parser()
