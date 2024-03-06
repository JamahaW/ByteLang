import utils
import bytelang5


def main():
    compiler = bytelang5.ByteLangCompiler()

    compiler.addPackage(r"A:\Projects\ByteLang\BetaPy\pack\test.blp")
    compiler.usePackage("test")

    print("\n".join(map(str, compiler.used_package.instructions.values())))

    input_path: str = "A:/Projects/ByteLang/test/tester.bls"
    output_path: str = "A:/Projects/ByteLang/test/tester.blc"

    try:
        compiler.execute(input_path, output_path)

    except bytelang5.ByteLangError as e:
        print(e)

    print(list(utils.File.readBinary(output_path)))

    return


main()
