from pathlib import PurePath

from bytelang.processors import Compiler

if __name__ == '__main__':
    base_folder = PurePath(r"A:\Projects\ByteLang")
    data_folder = base_folder / "data"

    compiler = Compiler()
    compiler.setPrimitivesFile(data_folder / "primitives/basic.json")
    compiler.setPackagesFolder(data_folder / "packages")
    compiler.setProfilesFolder(data_folder / "profiles")
    compiler.setEnvironmentsFolder(data_folder / "environments")

    compiler.run(base_folder / "examples_test/test.bls")
    print(compiler.getErrorsLog())
