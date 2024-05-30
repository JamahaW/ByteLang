from bytelang.makers import Compiler
from bytelang.tools import FileTool, ReprTool


def main():
    compiler = Compiler("../packages/", "../platforms/")
    source = FileTool.read("../code/tester.bls")

    compiler.run(source)

    print(list(compiler.getProgram()))
    print(ReprTool.column(compiler.getStatements()))
    print(ReprTool.column(compiler.getInstructions()))
    print(ReprTool.column(compiler.packages.current.INSTRUCTIONS.values()))
    print(ReprTool.column(compiler.code_generator.consts.items()))
    print(ReprTool.column(compiler.variables.values()))

    # input()


main()
