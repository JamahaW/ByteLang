from typing import Iterable

from bytelang.errors import ByteLangError
from bytelang.makers import Compiler
from bytelang.utils import File


def printIterable(i: Iterable):
    print('\n'.join(map(str, i)))


def main():
    compiler = Compiler("A:/Projects/ByteLang/packages/", "A:/Projects/ByteLang/platforms/")
    source = File.read("../code/tester.bls")

    try:
        program = compiler.run(source)
        print(list(program))
        File.saveBinary("../code/tester.blc", program)

    except ByteLangError as e:
        print(e)

    else:
        printIterable(compiler.environment.program.constants.items())
        printIterable(compiler.environment.program.variables.values())


main()
