import json
import pprint
import random
from user import User
from cell import Cell

class UserExists(Exception):
    pass

class UserNotFound(Exception):
    pass

class GameAlreadyStarted(Exception):
    pass

class GameCommandNotFound(Exception):
    pass

class AlreadyRolled(Exception):
    pass

class NotRolled(Exception):
    pass

class Board:

    def __init__(self, file: str) -> None:
        self.constructor(file)

    def constructor(self, file: str) -> None:
        with open(file, "r") as f:
            data = json.load(f)
        
        self.users = {}
        self.gamestarted = False
        self.userslist = [] #list to determine order of turns, set when game starts, sorted to make sure its deterministic
        self.turncounter = 0

        self.cells = [Cell(i) for i in data["cells"]]
        self.chance = data["chances"]
        self.startup = data["startup"]
        self.upgrade = data["upgrade"]
        self.tax = data["tax"]
        self.jailbail = data["jailbail"]
        self.teleport = data["teleport"]
        self.lottery = data["lottery"]

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
        elif self.gamestarted:
            raise GameAlreadyStarted #TODO: Handle
        else:
            user.attachedboard = self
            self.users[user.username] = user

    def detach(self, user: User) -> None:
        if user.username in self.users:
            user.attachedboard = None
            del self.users[user.username]

            if self.gamestarted:
                pass #TODO: Terminate game
        else:
            raise UserNotFound
    
    def ready(self, user: User) -> None:
        self.users[user.username].status.ready = True

        if all([self.users[u].status.ready for u in self.users]):
            for usr in self.users:
                self.users[usr].status.location_index = 0
                self.users[usr].status.money = self.startup

            self.gamestarted = True
            self.userslist = [self.users[usr] for usr in self.users]
            self.userslist.sort(key=lambda x: x.username)
            print(self.userslist)
            self.userslist[self.turncounter % len(self.userslist)].status.isplaying = True


    def turn(self, user: User, command: str) -> None:
        if command == "roll": #TODO: Increase money when start is passed (modulo)
            if not user.status.rolled:
                move = random.randint(1,6)
                print(user.username, "tossed", move)
                user.status.location_index += move
                user.status.location_index %= len(self.cells)
                print(f"{user.username} landed on ", self.cells[user.status.location_index].type)
                user.status.rolled = True
            else:
                raise AlreadyRolled

        elif command == "buy":
            pass
        elif command == "upgrade":
            pass
        elif command == "pick":
            pass
        elif command == "bail":
            pass
        elif command == "teleport":
            pass
        elif command == "end": #Additional
            if user.status.rolled:
                user.status.isplaying = False
                user.status.rolled = False
                self.turncounter += 1
                self.userslist[self.turncounter % len(self.userslist)].status.isplaying = True
            else:
                raise NotRolled
        else:
            raise GameCommandNotFound

    def getuserstate(self, user: User) -> str:
        return pprint.pformat(self.users[user.username].getstatus())

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
