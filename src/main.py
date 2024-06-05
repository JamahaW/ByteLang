from bytelang.makers import Compiler
from bytelang.tools import FileTool
from bytelang.vm.interpreter import Interpreter

compiler = Compiler("../packages/", "../platforms/")
interpreter = Interpreter()


def test(filename: str):
    compiler.run(FileTool.read(f"../test/{filename}.bls"))
    FileTool.save(f"../test/{filename}.txt", (
        compiler.errors.getLog()
        if compiler.errors.has() else
        compiler.getCompileLog(code=True, constants=True, variables=True, info=True, program=True)
    ))


def main():
    test("calcexpr")
    program = compiler.getProgram()
    interpreter.run(program, compiler.platforms.current)


main()
