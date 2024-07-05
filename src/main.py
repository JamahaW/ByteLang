from pathlib import PurePath

from bytelang import ByteLang
from bytelang.processors import LogFlag
from bytelang.tools import FileTool

# Рабочие папки
base_folder = PurePath(r"A:\Projects\ByteLang")
data_folder = base_folder / "data"
in_folder = base_folder / "examples"
out_folder = in_folder / 'out'

# Структура ByteLang позволяет создавать несколько экземпляров исполнителей
bl = ByteLang()
bl.setPrimitivesFile(data_folder / "primitives/std.json")
bl.setPackagesFolder(data_folder / "packages")
bl.setProfilesFolder(data_folder / "profiles")
bl.setEnvironmentsFolder(data_folder / "environments")


def run(filename: str, log_flags: LogFlag = LogFlag.ALL):
    """Запустить компиляцию файла, вывести логи и ошибки"""
    out = out_folder / f"{filename}.blc"
    result = bl.compile(in_folder / filename, out)
    status, log = ("Успешно", result.getInfoLog(log_flags)) if result else ("Неуспешно", bl.getErrorsLog())
    FileTool.save(f"{out}.txt", log)
    print(f"Компиляция завершена {status} {out}")


run("test_vm.bls", LogFlag.CONSTANTS | LogFlag.BYTECODE | LogFlag.ENVIRONMENT_INSTRUCTIONS)


vm = bl.getInterpreter("test_env", out_folder / "test_vm.bls.blc")
vm.run()
