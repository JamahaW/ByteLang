import silangcompilier


class App:

    def __init__(self):
        self.__parser = silangcompilier.Parser()

    def run(self):
        while True:
            statement = input("|>  ")
            try:
                print(f"= {self.getResult(statement)}")
            except Exception as e:
                print(f"Err: {e}")

    def getResult(self, statement: str):
        self.__parser.getTokenizer().load(statement)
        return self.__parser.calculate()


if __name__ == '__main__':
    App().run()
