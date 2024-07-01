from bytelang.processors import Compiler

if __name__ == '__main__':
    compiler = Compiler()
    compiler.setPrimitivesFile(r"A:\Project\ByteLang\registries_data\primitive_types.json")
    compiler.setEnvironmentsFolder(r"A:\Projects\ByteLang\registries_data\environments")
    compiler.setProfilesFolder(r"A:\Projects\ByteLang\registries_data\profiles")
    compiler.setPackagesFolder(r"A:\Projects\ByteLang\registries_data\packages")

    p = compiler.packageRegistry.get("math")
    print(p)

    pass
