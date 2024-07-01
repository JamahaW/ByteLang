from pathlib import PurePath

from bytelang.processors import Compiler
from bytelang.tools import ReprTool

if __name__ == '__main__':
    data_folder = PurePath(r"A:\Projects\ByteLang\registries_data")

    compiler = Compiler()
    compiler.setPrimitivesFile(data_folder / "primitive_types.json")
    compiler.setEnvironmentsFolder(data_folder / "environments")
    compiler.setProfilesFolder(data_folder / "profiles")
    compiler.setPackagesFolder(data_folder / "packages")

    # p = compiler.packageRegistry.get("math")
    print(ReprTool.column(compiler.primitiveTypeRegistry.getValues()))
