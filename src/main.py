from pathlib import PurePath

from bytelang.processors import ByteLang
from bytelang.processors import LogInfo
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


def run(filename: str, log_flags: LogInfo = LogInfo.ALL):
    """Запустить компиляцию файла, вывести логи и ошибки"""
    out = out_folder / f"{filename}.blc"
    result = bl.compile(in_folder / filename, out)
    log = result.getInfoLog(log_flags) if result else bl.getErrorsLog()
    status = "Успешно" if result else "Неуспешно"
    FileTool.save(f"{out}.txt", log)
    print(f"Компиляция завершена {status} {out}")


run("inc_test.bls", LogInfo.PROGRAM_VALUES | LogInfo.BYTECODE)
