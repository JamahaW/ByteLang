from typing import Iterable

from bytelang.errors import ByteLangError
from bytelang.makers import Compiler
from bytelang.utils import FileHelper


def printIterable(i: Iterable):
    print('\n'.join(map(str, i)))


def main():
    compiler = Compiler("../packages/", "../platforms/")
    source = FileHelper.read("../code/tester.bls")

    try:
        compiler.run(source)
        print(list(compiler.getProgram()))
        printIterable(compiler.getStatements())
        # File.saveBinary("../code/tester.blc", program)

    except ByteLangError as e:
        print(e)

    else:
        printIterable(compiler.environment.consts.items())
        printIterable(compiler.environment.variables.values())
        
    # input()


main()
