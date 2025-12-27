from bytelang import Lexer

_source_1 = """
//!math.bl
pub fn add(ret: *i16, a: *i16, b: *i16) void = 0x00

//!sketch.bl
import math

var x: i16 = 20
var result: i16

// амо
// гус

fn calculate(a: i16, b: i16) i16 {
    var sum: i16
    math.add(sum, a, b)
    return sum
}

fn main() void {
    result = calculate(100, x)
}
"""


def _lexer_run(name: str, source: str):
    lexer = Lexer(name, source)
    lexer.process()
    tokens = lexer.tokens()

    if tokens is None:
        print('\n'.join(map(str, lexer.errors())))
        return

    for __token in tokens:
        print(__token)

    return


_lexer_run("test", _source_1)
