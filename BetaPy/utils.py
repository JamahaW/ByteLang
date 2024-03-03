class File:

    @staticmethod
    def read(filepath: str):
        file = open(filepath)
        ret = file.read()
        file.close()
        return ret

    @staticmethod
    def save(filepath: str, data: str | bytes, mode: str):
        file = open(file=filepath, mode=mode)
        file.write(data)
        file.close()
