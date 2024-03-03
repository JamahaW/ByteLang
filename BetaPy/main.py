import bytelang5
import utils


def main():

    compiler = bytelang5.ByteLangCompiler()

    input_path: str = "A:/Projects/ByteLang/test/tester.bl"
    source: str = utils.File.read(input_path)

    program: bytes = compiler.execute(source)
    print(program)

    output_path: str = "A:/Projects/ByteLang/test/tester.blc"
    # utils.File.save(output_path, program, "wb")

    return
   
   
main()
