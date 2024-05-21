import sys

import bytelang4


def main():
    bytelang_compiler = bytelang4.Compiler(
        r"A:\Projects\ScriptingLanguage\MobileRobotics\data/bytelang/",
        "settings.json",
        [
            "basic.json",
            "algebraic.json",
            "stack.json",
            "branching.json",
            "robot.json",
        ]
    )
    # bytelang_compiler.generateExternalSourceCode("data/bytelang/source.h")
    # print(bytelang_compiler.getCommands())
    path = "A:\\Projects\\legacy\\ByteLangVirtualMashine\\bin\\debug\\"
    name = sys.argv[-1]
    try:
        program = bytelang_compiler.compile(
            f"{path}{name}.txt",
            f"{path}{name}.dat"
        )

    except bytelang4.ByteLangBaseError as BLBE:
        print(BLBE)

    else:
        print(bytelang_compiler.getLog())
        print(f"Программа скомпилирована\n{list(program)}")


if __name__ == "__main__":
    main()
