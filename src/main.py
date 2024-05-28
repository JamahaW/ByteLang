from typing import Iterable

from bytelang.errors import ByteLangError
from bytelang.makers import Compiler
from bytelang.utils import File


def printIterable(i: Iterable):
    print('\n'.join(map(str, i)))


def main():
    compiler = Compiler("../packages/", "../platforms/")
    source = File.read("../code/tester.bls")

    try:
        program = compiler.run(source)
        print(list(program))
        # File.saveBinary("../code/tester.blc", program)

    except ByteLangError as e:
        print(e)

    else:
        printIterable(compiler.environment.consts.items())
        printIterable(compiler.environment.variables.values())
        
    input()


main()
