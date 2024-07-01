from bytelang.processors import Compiler

if __name__ == '__main__':
    compiler = Compiler()
    compiler.setEnvironmentsFolder(r"A:\Projects\ByteLang\registries_data\environments/")
    compiler.setProfilesFolder(r"A:\Projects\ByteLang\registries_data\profiles/")
    compiler.setPackagesFolder(r"A:\Projects\ByteLang\registries_data\packages/")

    pass
