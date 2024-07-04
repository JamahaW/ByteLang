from pathlib import PurePath

from bytelang.processors import ByteLang
from bytelang.tools import FileTool

if __name__ == '__main__':
    base_folder = PurePath(r"A:\Projects\ByteLang")
    data_folder = base_folder / "data"
    out_folder = base_folder / 'out'

    bl = ByteLang()
    bl.setPrimitivesFile(data_folder / "primitives/basic.json")
    bl.setPackagesFolder(data_folder / "packages")
    bl.setProfilesFolder(data_folder / "profiles")
    bl.setEnvironmentsFolder(data_folder / "environments")


    def run(f_in: str):
        out = out_folder / f"{f_in}.blc"
        result = bl.compile(base_folder / "examples_test" / f_in, out)

        if errors := bl.getErrorsLog():
            FileTool.save(f"{out}_errors.txt", errors)

        FileTool.save(f"{out}_log.txt", result.getInfoLog())

    run("fib.bls")
