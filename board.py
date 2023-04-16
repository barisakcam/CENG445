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

class NotProperty(Exception):
    pass

class NotTeleport(Exception):
    pass

class NotJail(Exception):
    pass

class PropertyOwned(Exception):
    pass

class PropertyNotOwned(Exception):
    pass

class PropertyMaxLevel(Exception):
    pass

class NotEnoughMoney(Exception):
    pass

class InsufficientArguments(Exception):
    pass

class MustPick(Exception):
    pass

class MustTeleport(Exception):
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
        self.chance_index = 0
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
            self.userslist = [self.users[usr] for usr in self.users]
            self.userslist.sort(key=lambda x: x.username)

            for usr in self.users:
                #usr.start_game(self)
                self.users[usr].status.location_index = 0
                self.users[usr].status.money = self.startup
            
            self.gamestarted = True
            self.userslist[0].status.isplaying = True

            self.sendcallbacks(f"Game started. Turn order: {self.userslist}.")
            self.sendturncb(self.userslist[0], f"Your turn. Possible commands: {self.getpossiblemoves(self.userslist[0])}")


    def turn(self, user: User, command: str, newcell=None, pick=None) -> None:
        if command == "roll": #TODO: Increase money when start is passed (modulo)
            if not user.status.rolled:
                dice1 = random.randint(1,6)
                dice2 = random.randint(1,6)
                move = dice1 + dice2

                self.sendcallbacks(f"{user.username} tossed {dice1}, {dice2}")

                if user.status.jail:
                    if dice1 == dice2:
                        self.sendcallbacks(f"{user.username} tossed double and released.")
                        user.status.jail = False
                    else:
                        self.sendcallbacks(f"{user.username} failed to toss double and must wait for the next turn.")
                        user.status.jail = False
                        return
                
                user.status.location_index += move
                user.status.location_index %= len(self.cells)
                self.sendcallbacks(f"{user.username} landed on {user.status.location_index}, which is type {self.cells[user.status.location_index].type}")

                if move > user.status.location_index:
                    #TODO: is salary amount specified? self.lottery for now
                    self.sendcallbacks(f"{user.username} passed start and received {self.lottery}")
                    user.status.money += self.lottery

                user.status.rolled = True

                if self.cells[user.status.location_index].type == "chance card": #other chance cards need pick
                    self.sendcallbacks(f"{user.username} drew {self.chance[self.chance_index]}")

                    if self.chance[self.chance_index]["type"] == "goto jail":
                        while not self.cells[user.status.location_index].type == "jail":
                            user.status.location_index += 1
                            user.status.location_index %= len(self.cells)

                        self.sendcallbacks(f"{user.username} is jailed in cell {user.status.location_index}")
                        user.status.jail = True

                    elif self.chance[self.chance_index]["type"] == "tax":
                        self.sendcallbacks(f"{user.username} paid {self.tax * len(user.status.properties)} tax")
                        user.status.money -= self.tax * len(user.status.properties)

                    elif self.chance[self.chance_index]["type"] == "lottery":
                        self.sendcallbacks(f"{user.username} won {self.lottery} lottery")
                        user.status.money += self.lottery

                    elif self.chance[self.chance_index]["type"] == "jail free":
                        self.sendcallbacks(f"{user.username} gained a jail free card")
                        user.status.jailcards += 1

                    elif self.chance[self.chance_index]["type"] == "upgrade":
                        if len(user.status.properties) == 0:
                            self.sendcallbacks(f"{user.username} can not upgrade since user does not own a property.")
                        else:
                            user.status.pick = True

                    elif self.chance[self.chance_index]["type"] == "downgrade":
                        if len(user.status.properties) == 0:
                            self.sendcallbacks(f"{user.username} can not downgrade since user does not own a property.")
                        else:
                            user.status.pick = True

                    elif self.chance[self.chance_index]["type"] == "color upgrade":
                        if len(user.status.properties) == 0:
                            self.sendcallbacks(f"{user.username} can not color upgrade since user does not own a property.")
                        else:
                            user.status.pick = True

                    elif self.chance[self.chance_index]["type"] == "color downgrade":
                        if len(user.status.properties) == 0:
                            self.sendcallbacks(f"{user.username} can not color downgrade since user does not own a property.")
                        else:
                            user.status.pick = True

                    elif self.chance[self.chance_index]["type"] == "teleport":
                        user.status.teleport = True

                    self.chance_index = (self.chance_index+1) % len(self.chance)

                elif self.cells[user.status.location_index].type == "goto jail":
                    while not self.cells[user.status.location_index].type == "jail":
                        user.status.location_index += 1
                        user.status.location_index %= len(self.cells)

                    self.sendcallbacks(f"{user.username} is jailed in cell {user.status.location_index}")
                    user.status.jail = True

                elif self.cells[user.status.location_index].type == "tax":
                    self.sendcallbacks(f"{user.username} paid {self.tax * len(user.status.properties)} tax")
                    user.status.money -= self.tax * len(user.status.properties)
                    
                elif self.cells[user.status.location_index].type == "jail":
                    self.sendcallbacks(f"{user.username} is jailed in cell {user.status.location_index}")
                    user.status.jail = True

                elif self.cells[user.status.location_index].type == "property":
                    if user.status.money < self.cells[user.status.location_index].property.rents[self.cells[user.status.location_index].property.level - 1]:
                        self.users[self.cells[user.status.location_index].property.owner].money += user.status.money
                        user.status.money = 0

                        self.sendturncb(user, f'{user.username} could not paid rent and bankrupted.')

                        self.gameover()
                    else:
                        self.users[self.cells[user.status.location_index].property.owner].money += self.cells[user.status.location_index].property.rents[self.cells[user.status.location_index].property.level - 1]
                        user.status.money -= self.cells[user.status.location_index].property.rents[self.cells[user.status.location_index].property.level - 1]
                        self.sendturncb(user, f'{user.username} paid {self.cells[user.status.location_index].property.rents[self.cells[user.status.location_index].property.level - 1]} rent to {self.users[self.cells[user.status.location_index].property.owner].username}.')

                elif self.cells[user.status.location_index].type == "teleport":
                    user.status.teleport = True

                self.sendturncb(user, f'Possible moves are: {self.getpossiblemoves(user)}')

            else:
                raise AlreadyRolled

        elif command == "buy":
            if user.status.rolled:
                if self.cells[user.status.location_index].type == "property":
                    if self.cells[user.status.location_index].property.owner is None:
                        if user.status.money >= self.cells[user.status.location_index].property.price:
                            user.status.money -= self.cells[user.status.location_index].property.price
                            user.status.properties.append(self.cells[user.status.location_index].property)
                            self.cells[user.status.location_index].property.owner = user.username
                            self.sendcallbacks(f"{user.username} bought {self.cells[user.status.location_index].property.name}.")
                        else:
                            raise NotEnoughMoney
                    else:
                        raise PropertyOwned
                else:
                    raise NotProperty
            else:
                raise NotRolled
        elif command == "upgrade":
            if user.status.rolled:
                if self.cells[user.status.location_index].property.owner == user.username:
                    if self.cells[user.status.location_index].property.level < 5:
                        if user.status.money >= self.upgrade:
                            user.status.money -= self.upgrade
                            self.cells[user.status.location_index].property.level += 1
                            self.sendcallbacks(f"{user.username} upgraded {self.cells[user.status.location_index].property.name} to level {self.cells[user.status.location_index].property.level}.")
                        else:
                            NotEnoughMoney
                    else:
                        PropertyMaxLevel
                else:
                    PropertyNotOwned
            else:
                raise NotRolled
        elif command == "pick":
            pass
        elif command == "bail":
            if not user.status.rolled:
                if self.cells[user.status.location_index].type == "jail":
                    if user.status.money >= self.jailbail:
                        user.status.money -= self.cells[user.status.location_index].property.price
                        user.status.properties.append(self.cells[user.status.location_index].property)
                        self.cells[user.status.location_index].property.owner = user.username

                        print(f"{user.username} bailed")
                        user.status.jail = False
                    else:
                        raise NotEnoughMoney
                else:
                    raise NotJail
            else:
                raise AlreadyRolled
        elif command == "teleport":
            if user.status.rolled:
                if user.status.teleport:
                    if user.status.money >= self.teleport:
                        user.status.money -= self.teleport
                        user.status.location_index = int(newcell)
                        print(f"{user.username} teleported to ", self.cells[int(newcell)].type)
                        user.status.teleport = False
                    else:
                        raise NotEnoughMoney
                else:
                    raise NotTeleport
            else:
                raise NotRolled
        elif command == "end": #Additional
            if user.status.rolled:
                if not user.status.teleport:
                    if not user.status.pick:
                        user.status.isplaying = False
                        user.status.rolled = False
                        self.turncounter += 1
                        self.turncounter %= len(self.userslist)
                        self.userslist[self.turncounter].status.isplaying = True
                        self.sendturncb(self.userslist[self.turncounter], f"Your turn. Possible commands: {self.getpossiblemoves(self.userslist[self.turncounter])}")
                    else:
                        MustPick
                else:
                    MustTeleport
            else:
                raise NotRolled
        else:
            raise GameCommandNotFound

    def getuserstate(self, user: User) -> str:
        return pprint.pformat(self.users[user.username].getstatus())

    def getboardstate(self) -> str:
        return pprint.pformat({"cells": [cell.get() for cell in self.cells],
                               "users": [username for username in self.users]}, sort_dicts=False)
    
    def sendcallbacks(self, message: str) -> None:
        for usr in self.users:
            self.users[usr].callback(message)

    def sendturncb(self, user: User, message: str) -> None:
        user.turncb(message)

    def getpossiblemoves(self, user: User) -> list:
        result = []

        if user.status.rolled:
            if self.cells[user.status.location_index].type == "jail":
                result.append("bail")

            if self.cells[user.status.location_index].type == "property":
                if self.cells[user.status.location_index].property.owner is None:
                    result.append("buy")
                if self.cells[user.status.location_index].property.owner == user.username:
                    result.append("upgrade")

            if user.status.teleport:
                result.append("teleport")

            if user.status.pick:
                result.append("pick")

            if self.cells[user.status.location_index].type == "chance card":
                pass

            if not user.status.teleport and not user.status.pick:
                result.append("end")

        else:
            result.append("roll")

            if user.status.jail:
                result.append("bail")

        return result
    
    def gameover() -> None:
        print("GAME OVER") #TODO

    def __repr__(self) -> str:
        for i in self.cells:
            print(i)
        #for i in self.users:
            #print(i) 
    
# For testing
if __name__ == "__main__":
    board = Board("input.json")
