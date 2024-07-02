from pathlib import PurePath

from bytelang.processors import Compiler

if __name__ == '__main__':
    base_folder = PurePath(r"A:\Projects\ByteLang")
    data_folder = base_folder / "registries_data"

    compiler = Compiler()
    compiler.setPrimitivesFile(data_folder / "primitive_types.json")
    compiler.setEnvironmentsFolder(data_folder / "environments")
    compiler.setProfilesFolder(data_folder / "profiles")
    compiler.setPackagesFolder(data_folder / "packages")

    compiler.run(base_folder / "test/test.bls")
    print(compiler.getErrorsLog())
