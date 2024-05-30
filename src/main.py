from typing import Iterable

from bytelang.errors import ByteLangError
from bytelang.makers import Compiler
from bytelang.tools import FileTool


def printi(i: Iterable):
    print('\n'.join(map(str, i)))


def main():
    compiler = Compiler("../packages/", "../platforms/")
    source = FileTool.read("../code/tester.bls")

    try:
        compiler.run(source)
        print(list(compiler.getProgram()))
        printi(compiler.getStatements())
        printi(compiler.getInstructions())

    except ByteLangError as e:
        print(e)

    else:
        printi(compiler.packages.current.INSTRUCTIONS.values())
        printi(compiler.code_generator.consts.items())
        printi(compiler.variables.values())
        
    # input()


main()
