import json
import user

class Board:

    def __init__(self, file: str) -> None:
        self.constructor(file)

    def constructor(self, file: str) -> None:
        with open(file, "r") as f:
            data = json.load(f)
            
        self.cells = data["cells"]

    def attach(self, user, callback, turncb) -> None:
        """TODO"""
        pass

    def detach(self, user) -> None:
        """TODO"""
        pass
    
    def ready(self, user) -> None:
        """TODO"""
        pass

    def turn(self, user, command) -> None:
        """TODO"""
        pass

    def getuserstate(self, user) -> None:
        """TODO"""
        pass

    def getboardstate(self) -> str:
        """TODO"""
        pass

# For testing
if __name__ == "__main__":
    board = Board("input.json")
