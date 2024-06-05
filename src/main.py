from bytelang.makers import Compiler
from bytelang.tools import FileTool, ReprTool

compiler = Compiler("../packages/", "../platforms/")


def getCompilerOutput(source: str) -> str:
    compiler.run(source)

    if compiler.errors.has():
        return compiler.errors.getLog()

    return compiler.getCompileLog(code=True, constants=True, variables=True, sizes=True, program=True)


def test(filename: str, out: str):
    FileTool.save(f"../test/{out}.txt", getCompilerOutput(FileTool.read(f"../test/{filename}.bls")))


def main():
    test_files = tuple(FileTool.getFileNamesByExt("../test/", "bls"))
    print(ReprTool.column(test_files))

    # test("m", "m")

    for file in test_files:
        test(file, file)


main()
