from bytelang.makers import Compiler
from bytelang.tools import FileTool
from bytelang.vm.interpreter import Interpreter

# TODO
#  внедрить в платформу конфигурацию пакетов команд
#  Сменить название директивы platform

# TODO Продвинутый синтаксис, расчёт константных выражений

compiler = Compiler("../packages/", "../platforms/")


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

    interpreter = Interpreter()
    interpreter.run(program, compiler.platforms.current)


main()
