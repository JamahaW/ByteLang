from pathlib import PurePath

from bytelang.processors import ByteLang

if __name__ == '__main__':
    base_folder = PurePath(r"A:\Projects\ByteLang")
    data_folder = base_folder / "data"

    bl = ByteLang()
    bl.setPrimitivesFile(data_folder / "primitives/basic.json")
    bl.setPackagesFolder(data_folder / "packages")
    bl.setProfilesFolder(data_folder / "profiles")
    bl.setEnvironmentsFolder(data_folder / "environments")

    result = bl.compile(base_folder / "examples_test/test.bls")
    print(bl.getErrorsLog())
    print(result)
