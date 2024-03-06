from bytelang import bytelang5, utils, errors


def main():
    compiler = bytelang5.ByteLangCompiler()

    compiler.packages.load(r"A:\Projects\ByteLang\pack\test.blp")
    compiler.packages.use("test")
    print(compiler.packages.used)

    compiler.platforms.load(r"A:\Projects\ByteLang\platforms\test.json")
    compiler.platforms.use("test")
    print(compiler.platforms.used)

    input_path: str = "A:/Projects/ByteLang/code/tester.bls"
    output_path: str = "A:/Projects/ByteLang/code/tester.blc"

    try:
        compiler.execute(input_path, output_path)

    except errors.ByteLangError as e:
        print(e)

    print(list(utils.File.readBinary(output_path)))

    return


main()
