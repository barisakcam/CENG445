import json
from user import User
from cell import Cell

class Board:

    def __init__(self, file: str) -> None:
        self.constructor(file)

    def constructor(self, file: str) -> None:
        with open(file, "r") as f:
            data = json.load(f)
        
        self.cells = []
        for i in data["cells"]:
            self.cells.append(Cell(i))
        #userların kendisi dictionary zaten liste iş görür gibi sanki
        self.users = []
        self.chance = data["chances"]
        

    def delete(self) -> None:
        self.cells = []
        self.users = []
        self.chance = {}

    def update(self, file: str) -> None:
        self.delete()
        self.constructor(file)

    def attach(self, user, callback, turncb) -> None:
        """TODO"""
        pass

    def detach(self, user) -> None:
        """TODO"""
        pass
    
    def ready(self, user) -> None:
        for i in self.users:
            if user.username == i.username:
                i.ready = True

    def turn(self, user, command) -> None:
        """TODO"""
        pass

    def getuserstate(self, user) -> None:
        """TODO"""
        pass

    def getboardstate(self) -> str:
        """TODO"""
        pass

    def __repr__(self) -> str:
        for i in self.cells:
            print(i)
        #for i in self.users:
            #print(i) 
    
# For testing
if __name__ == "__main__":
    board = Board("input.json")
