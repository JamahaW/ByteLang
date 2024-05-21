from typing import Iterable

from bytelang import core as bl, utils


def printIterable(i: Iterable):
    print('\n'.join(map(str, i)))


def main():
    env = bl.Environment()

    env.packages.load("A:/Projects/ByteLang/packages/test_package.blp")
    env.packages.use("test_package")

    env.platforms.load("A:/Projects/ByteLang/platforms/test_platform.json")
    env.platforms.use("test_platform")

    input_path = "../code/tester.bls"

    source = utils.File.read(input_path)

    try:
        tokeniser = bl.Tokeniser(env)
        statements = tokeniser.run(source)

        # printIterable(statements)

        parser = bl.Parser(env)
        stu = parser.run(statements)

        printIterable(stu)
        printIterable(env.program.constants.items())
        printIterable(env.program.variables.values())

        compiler = bl.Compiler(env)
        prog = compiler.run(stu)
        print(list(prog))

    except bl.ByteLangError as e:
        print(e)


main()

# output_path = "../code/tester.blc"
