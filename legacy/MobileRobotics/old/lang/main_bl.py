import bytelang4
import utils


def main():
    bytelang.LangProcessor_OLD.Init(utils.File.readJSON("../assets/data/settings.json"))

    # bytelang.LangProcessor.GenerateNativeVM("data/commands.txt")

    processor = bytelang.LangProcessor_OLD()

    # state = processor.simpleCompileSave("test/test.bl", "test/out.hex")
    # print(utils.String.listToTable(state))

    program = processor.compile(utils.File.read("../assets/test/test.bl"))
    print(list(program))


if __name__ == "__main__":
    main()
