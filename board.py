import json
import pprint
from user import User
from cell import Cell

class UserExists(Exception):
    pass

class UserNotFound(Exception):
    pass

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
        self.users = {}
        self.chance = data["chances"]

    def delete(self) -> None:
        self.cells = []
        self.users = {}
        self.chance = {}

    def update(self, file: str) -> None:
        self.delete()
        self.constructor(file)

    def attach(self, user: User) -> None:
        if user.username in self.users:
            raise UserExists
        else:
            self.users[user.username] = user

    def detach(self, user: User) -> None:
        if user.username in self.users:
            del self.users[user.username]
        else:
            raise UserNotFound
    
    def ready(self, user) -> None:
        self.users[user.username].ready = True

    def turn(self, user, command) -> None:
        """TODO"""
        pass

    def getuserstate(self, user) -> str:
        return pprint.pformat(self.users[user.username])

    def getboardstate(self) -> str:
        return pprint.pformat({"cells": [cell.get() for cell in self.cells],
                               "users": [username for username in self.users]}, sort_dicts=False)

    def __repr__(self) -> str:
        for i in self.cells:
            print(i)
        #for i in self.users:
            #print(i) 
    
# For testing
if __name__ == "__main__":
    board = Board("input.json")
