from pathlib import PurePath

from bytelang.processors import Compiler
from bytelang.tools import ReprTool

if __name__ == '__main__':
    base_folder = PurePath(r"A:\Projects\ByteLang")
    data_folder = base_folder / "data"

    compiler = Compiler()
    compiler.setPrimitivesFile(data_folder / "primitives/basic.json")
    compiler.setEnvironmentsFolder(data_folder / "environments")
    compiler.setProfilesFolder(data_folder / "profiles")
    compiler.setPackagesFolder(data_folder / "packages")

    compiler.run(base_folder / "examples_test/test.bls")
    print(compiler.getErrorsLog())

    # print(ReprTool.column(compiler.primitive_type_registry.getValues()))
