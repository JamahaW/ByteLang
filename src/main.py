from os import PathLike
from pathlib import PurePath

from bytelang import ByteLang
from bytelang.interpreters import INSTRUCTIONS
from bytelang.interpreters import Interpreter
from bytelang.processors import LogFlag
from bytelang.tools import FileTool

# Рабочие папки
base_folder = PurePath(r"A:\Projects\ByteLang")
data_folder = base_folder / "data"
in_folder = base_folder / "examples"
out_folder = in_folder / 'out'

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
    vm = Interpreter(bl.environment_registry.get(env), bl.primitives_registry, INSTRUCTIONS)
    ret = vm.run(bytecode_filepath)
    print(f"Программа Bytelang завершена с кодом {ret}")


run("test_vm.bls", LogFlag.CONSTANTS | LogFlag.BYTECODE | LogFlag.ENVIRONMENT_INSTRUCTIONS)
execute(out_folder / "test_vm.bls.blc", "test_env")
