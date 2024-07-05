from os import PathLike
from pathlib import PurePath

from bytelang import ByteLang
from bytelang.interpreters import Interpreter
from bytelang.processors import LogFlag
from bytelang.tools import FileTool
from generated.test_gen import INSTRUCTIONS

# Рабочие папки
base_folder = PurePath(r"A:\Projects\ByteLang")
data_folder = base_folder / "data"
in_folder = base_folder / "examples"
out_folder = in_folder / 'out'
py_source_generated_folder = base_folder / "src/generated"

# Структура ByteLang позволяет создавать несколько экземпляров исполнителей
bl = ByteLang()
bl.primitives_registry.setFile(data_folder / "primitives/std.json")
bl.package_registry.setFolder(data_folder / "packages")
bl.profile_registry.setFolder(data_folder / "profiles")
bl.environment_registry.setFolder(data_folder / "environments")


def run(filename: str, log_flags: LogFlag = LogFlag.ALL) -> None:
    """Запустить компиляцию файла, вывести логи и ошибки"""
    out = out_folder / f"{filename}.blc"
    result = bl.compile(in_folder / filename, out)
    status, log = ("Успешно", result.getInfoLog(log_flags)) if result else ("Неуспешно", bl.getErrorsLog())
    FileTool.save(f"{out}.txt", log)
    print(f"Компиляция завершена {status} {out}")


def execute(bytecode_filepath: PathLike, env: str) -> None:
    """Исполнить байткод программу"""
    vm = Interpreter(bl.environment_registry.get(env), bl.primitives_registry, INSTRUCTIONS)
    ret = vm.run(bytecode_filepath)
    print(f"Программа Bytelang завершена с кодом {ret}")


def genSource(env: str):
    """Сгенерировать исходный код инструкций"""
    ret = bl.generateSource(env, py_source_generated_folder)
    print(f"Исходный код окружения {env} был создан в {ret}")


# run("test_gen.bls", LogFlag.CONSTANTS | LogFlag.BYTECODE)
genSource("test_env")
# execute(out_folder / "test_gen.bls.blc", "test_gen")
