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

class PickError(Exception):
    pass

class InvalidTeleport(Exception):
    pass

class CellIndexError(Exception):
    pass

class CellIndexError(Exception):
    pass

class PropertyOp(Exception):
    pass

# Exceptions are used to check error conditions. They are caught in demo applications and converted to print statements.
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
        self.users.clear()
        self.gamestarted = False
        self.userslist.clear()
        self.turncounter = 0

        self.cells.clear()
        self.chance.clear()
        self.chance_index = 0
        self.startup = 0
        self.upgrade = 0
        self.tax = 0
        self.jailbail = 0
        self.teleport = 0
        self.lottery = 0

    def update(self, file: str) -> None:
        with open(file, "r") as f:
            data = json.load(f)

        self.gamestarted = False
        self.userslist = [] # list to determine order of turns, set when game starts, sorted to make sure its deterministic
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

        # User states are reset since a new game starts with a new input file
        for user in self.users:
            self.users[user].reset()

    # Since callback and turncb are methods in User class, they are not given to attach seperately
    def attach(self, user: User) -> None:
        if user.username in self.users:
            raise UserExists
        elif self.gamestarted:
            raise GameAlreadyStarted
        else:
            user.attachedboard = self
            self.users[user.username] = user

    def detach(self, user: User) -> None:
        if user.username in self.users:
            user.attachedboard = None
            user.status.ready = False

            del self.users[user.username]

            if self.gamestarted:
                self.sendcallbacks(f"{user.username} detached.")
                self.gameover()
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
        if command == "roll":
            if not user.status.rolled:
                dice1 = random.randint(1,6)
                dice2 = random.randint(1,6)
                move = dice1 + dice2

                user.status.rolled = True
                self.sendcallbacks(f"{user.username} tossed {dice1}, {dice2}")

                if user.status.jail:
                    if dice1 == dice2:
                        self.sendcallbacks(f"{user.username} tossed double and released.")
                        user.status.jail = False
                    else:
                        self.sendcallbacks(f"{user.username} failed to toss double and must wait for the next turn.")
                        user.status.jail = False
                        self.turn(user, "end")
                        return
                
                user.status.location_index += move
                user.status.location_index %= len(self.cells)
                self.sendcallbacks(f"{user.username} landed on {user.status.location_index}, which is type {self.cells[user.status.location_index].type}")

                if move > user.status.location_index:
                    #TODO: is salary amount specified? self.lottery for now
                    self.sendcallbacks(f"{user.username} passed start and received {self.lottery}")
                    user.status.money += self.lottery

                if self.cells[user.status.location_index].type == "chance card": #other chance cards need pick
                    self.sendcallbacks(f"{user.username} drew {self.chance[self.chance_index]['type']}")

                    if self.chance[self.chance_index]["type"] == "goto jail":
                        while not self.cells[user.status.location_index].type == "jail":
                            user.status.location_index += 1
                            user.status.location_index %= len(self.cells)

                        self.sendcallbacks(f"{user.username} is jailed in cell {user.status.location_index}. {user.username} has {user.status.jailcards} jail free cards.")
                        user.status.jail = True

                    elif self.chance[self.chance_index]["type"] == "tax":
                        self.sendcallbacks(f"{user.username} paid {self.tax * len(user.status.properties)} tax")
                        user.status.money -= self.tax * len(user.status.properties)

                        if user.status.money < 0:
                            self.sendcallbacks(f'{user.username} could not paid tax and bankrupted.')
                            self.gameover()

                    elif self.chance[self.chance_index]["type"] == "lottery":
                        self.sendcallbacks(f"{user.username} won {self.lottery} lottery")
                        user.status.money += self.lottery

                    elif self.chance[self.chance_index]["type"] == "jail free":
                        user.status.jailcards += 1
                        self.sendcallbacks(f"{user.username} has {user.status.jailcards} jail free cards.")

                    elif self.chance[self.chance_index]["type"] == "upgrade":
                        if len(user.status.properties) == 0:
                            self.sendcallbacks(f"{user.username} can not upgrade since user does not own a property.")
                        else:
                            user.status.pick = "upgrade"

                    elif self.chance[self.chance_index]["type"] == "downgrade":
                        if len(user.status.properties) == 0:
                            self.sendcallbacks(f"{user.username} can not downgrade since user does not own a property.")
                        else:
                            user.status.pick = "downgrade"

                    elif self.chance[self.chance_index]["type"] == "color upgrade":
                        if len(user.status.properties) == 0:
                            self.sendcallbacks(f"{user.username} can not color upgrade since user does not own a property.")
                        else:
                            user.status.pick = "color upgrade"

                    elif self.chance[self.chance_index]["type"] == "color downgrade":
                        if len(user.status.properties) == 0:
                            self.sendcallbacks(f"{user.username} can not color downgrade since user does not own a property.")
                        else:
                            user.status.pick = "color downgrade"

                    elif self.chance[self.chance_index]["type"] == "teleport":
                        user.status.freeteleport = True

                    self.chance_index = (self.chance_index+1) % len(self.chance)

                elif self.cells[user.status.location_index].type == "goto jail":
                    while not self.cells[user.status.location_index].type == "jail":
                        user.status.location_index += 1
                        user.status.location_index %= len(self.cells)

                    self.sendcallbacks(f"{user.username} is jailed in cell {user.status.location_index}. {user.username} has {user.status.jailcards} jail free cards.")
                    user.status.jail = True

                elif self.cells[user.status.location_index].type == "tax":
                    self.sendcallbacks(f"{user.username} paid {self.tax * len(user.status.properties)} tax")
                    user.status.money -= self.tax * len(user.status.properties)

                    if user.status.money < 0:
                        self.sendcallbacks(f'{user.username} could not pay tax and bankrupted.')
                        self.gameover()
                    
                elif self.cells[user.status.location_index].type == "jail":
                    self.sendcallbacks(f"{user.username} is jailed in cell {user.status.location_index}. {user.username} has {user.status.jailcards} jail free cards.")
                    user.status.jail = True

                elif self.cells[user.status.location_index].type == "property":
                    if self.cells[user.status.location_index].property.owner is not None:
                        if self.cells[user.status.location_index].property.owner != user.username:
                            if not self.users[self.cells[user.status.location_index].property.owner].status.jail:
                                if user.status.money < self.cells[user.status.location_index].property.rents[self.cells[user.status.location_index].property.level - 1]:
                                    self.users[self.cells[user.status.location_index].property.owner].status.money += user.status.money
                                    user.status.money = 0
                                    self.sendcallbacks(f'{user.username} could not pay rent and bankrupted.')
                                    self.gameover()
                                else:
                                    self.users[self.cells[user.status.location_index].property.owner].status.money += self.cells[user.status.location_index].property.rents[self.cells[user.status.location_index].property.level - 1]
                                    user.status.money -= self.cells[user.status.location_index].property.rents[self.cells[user.status.location_index].property.level - 1]
                                    self.sendcallbacks(f'{user.username} paid {self.cells[user.status.location_index].property.rents[self.cells[user.status.location_index].property.level - 1]} rent to {self.cells[user.status.location_index].property.owner}.')
                            else:
                                self.sendcallbacks(f'{user.username} did not pay rent since {self.cells[user.status.location_index].property.owner} is in jail.')

                elif self.cells[user.status.location_index].type == "teleport":
                    user.status.paidteleport = True

                elif self.cells[user.status.location_index].type == "lottery":
                    self.sendcallbacks(f"{user.username} won {self.lottery} lottery")
                    user.status.money += self.lottery

            else:
                raise AlreadyRolled

        elif command == "buy":
            if user.status.rolled:
                if not user.status.propertyop:
                    if self.cells[user.status.location_index].type == "property":
                        if self.cells[user.status.location_index].property.owner is None:
                            if user.status.money >= self.cells[user.status.location_index].property.price:
                                user.status.money -= self.cells[user.status.location_index].property.price
                                user.status.properties.append(self.cells[user.status.location_index].property)
                                self.cells[user.status.location_index].property.owner = user.username
                                self.sendcallbacks(f"{user.username} bought {self.cells[user.status.location_index].property.name}.")
                                user.status.propertyop = True
                            else:
                                raise NotEnoughMoney
                        else:
                            raise PropertyOwned
                    else:
                        raise NotProperty
                else:
                    raise PropertyOp
            else:
                raise NotRolled
            
        elif command == "upgrade":
            if user.status.rolled:
                if not user.status.propertyop:
                    if self.cells[user.status.location_index].type == "property":
                        if self.cells[user.status.location_index].property.owner == user.username:
                            if self.cells[user.status.location_index].property.level < 5:
                                if user.status.money >= self.upgrade:
                                    user.status.money -= self.upgrade
                                    self.cells[user.status.location_index].property.level += 1
                                    self.sendcallbacks(f"{user.username} upgraded {self.cells[user.status.location_index].property.name} to level {self.cells[user.status.location_index].property.level}.")
                                    user.status.propertyop = True
                                else:
                                    raise NotEnoughMoney
                            else:
                                raise PropertyMaxLevel
                        else:
                            raise PropertyNotOwned
                    else:
                        raise NotProperty
                else:
                    raise PropertyOp
            else:
                raise NotRolled
            
        elif command == "pick":
            if user.status.pick is not None:
                if int(pick) < len(self.cells):
                    if self.cells[int(pick)].type == "property":
                        if self.cells[int(pick)].property.owner == user.username:
                            if user.status.pick == "upgrade":
                                if self.cells[int(pick)].property.level < 5:
                                    self.cells[int(pick)].property.level += 1
                                    self.sendcallbacks(f"{user.username} upgraded {self.cells[int(pick)].property.name} to level {self.cells[int(pick)].property.level}.")
                                else:
                                    self.sendcallbacks(f"{user.username} tried to upgrade {self.cells[int(pick)].property.name} but failed since it is max level.")
                            elif user.status.pick == "downgrade":
                                if self.cells[int(pick)].property.level > 1:
                                    self.cells[int(pick)].property.level -= 1
                                    self.sendcallbacks(f"{user.username} downgraded {self.cells[int(pick)].property.name} to level {self.cells[int(pick)].property.level}.")
                                else:
                                    self.sendcallbacks(f"{user.username} tried to downgrade {self.cells[int(pick)].property.name} but failed since it is level 1.")
                            elif user.status.pick == "color upgrade":
                                for cell in self.cells:
                                    if cell.type == "property" and cell.property.color == self.cells[int(pick)].property.color:
                                        if cell.property.level < 5:
                                            cell.property.level += 1
                                            self.sendcallbacks(f"{user.username} upgraded {cell.property.name} to level {cell.property.level}.")
                                        else:
                                            self.sendcallbacks(f"{user.username} tried to upgrade {cell.property.name} but failed since it is max level.")
                            elif user.status.pick == "color downgrade":
                                for cell in self.cells:
                                    if cell.type == "property" and cell.property.color == self.cells[int(pick)].property.color:
                                        if cell.property.level > 1:
                                            cell.property.level -= 1
                                            self.sendcallbacks(f"{user.username} downgraded {cell.property.name} to level {cell.property.level}.")
                                        else:
                                            self.sendcallbacks(f"{user.username} tried to downgrade {cell.property.name} but failed since it is level 1.")
                            
                            user.status.pick = None
                        else:
                            raise PropertyNotOwned
                    else:
                        raise NotProperty
                else:
                    raise CellIndexError
            else:
                raise PickError

        elif command == "bail":
            if not user.status.rolled:
                if self.cells[user.status.location_index].type == "jail":
                    if user.status.jailcards > 0:
                        user.status.jailcards -= 1
                        self.sendcallbacks(f"{user.username} bailed for a jail free card. {user.username} has {user.status.jailcards} jail free cards remaining.")
                        user.status.jail = False
                    else:
                        if user.status.money >= self.jailbail:
                            user.status.money -= self.jailbail
                            self.sendcallbacks(f"{user.username} bailed for {self.jailbail}.")
                            user.status.jail = False
                        else:
                            raise NotEnoughMoney
                else:
                    raise NotJail
            else:
                raise AlreadyRolled
            
        elif command == "teleport":
            if user.status.rolled:
                if int(newcell) < len(self.cells):
                    if user.status.paidteleport:
                        if user.status.money >= self.teleport:
                            if self.cells[int(newcell)].type == "property":
                                user.status.money -= self.teleport
                                user.status.location_index = int(newcell)
                                self.sendcallbacks(f"{user.username} teleported to {self.cells[int(newcell)].type}")
                                user.status.paidteleport = False
                            else:
                                raise InvalidTeleport
                        else:
                            raise NotEnoughMoney
                    elif user.status.freeteleport:
                        if self.cells[int(newcell)].type == "property":
                            user.status.location_index = int(newcell)
                            self.sendcallbacks(f"{user.username} teleported to {self.cells[int(newcell)].type}")
                            user.status.freeteleport = False
                        else:
                            raise InvalidTeleport
                    else:
                        raise NotTeleport
                else:
                    raise CellIndexError
            else:
                raise NotRolled
            
        # The end command is an additional command to end the users turn.
        # It is automatically called if there is no other possible command 
        elif command == "end":
            if user.status.rolled:
                if not user.status.freeteleport:
                    if user.status.pick is None:
                        user.status.isplaying = False
                        user.status.rolled = False
                        user.status.propertyop = False
                        self.turncounter += 1
                        self.turncounter %= len(self.userslist)
                        self.userslist[self.turncounter].status.isplaying = True
                        self.sendturncb(self.userslist[self.turncounter], f"Your turn. Possible commands: {self.getpossiblemoves(self.userslist[self.turncounter])}")
                    else:
                        raise MustPick
                else:
                    raise MustTeleport
            else:
                raise NotRolled
        
        else:
            raise GameCommandNotFound
        
        if command != "end":
            temp = self.getpossiblemoves(user)
            if len(temp) == 1 and temp[0] == "end":
                self.turn(user, "end") # Calling end since it is the only possible command
            else:
                self.sendturncb(user, f"Turn continues. Possible commands: {temp}")

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

    # Get possible moves to send turncb
    def getpossiblemoves(self, user: User) -> list:
        result = []

        if user.status.rolled:
            if not user.status.propertyop:
                if self.cells[user.status.location_index].type == "property":
                    if self.cells[user.status.location_index].property.owner is None:
                        result.append("buy")
                    if self.cells[user.status.location_index].property.owner == user.username:
                        if self.cells[user.status.location_index].property.level < 5:
                            result.append("upgrade")

            if user.status.freeteleport or user.status.paidteleport:
                result.append("teleport")

            if user.status.pick is not None:
                result.append("pick")

            if self.cells[user.status.location_index].type == "chance card":
                pass

            if not user.status.freeteleport and user.status.pick is None:
                result.append("end")

        else:
            result.append("roll")

            if user.status.jail:
                result.append("bail")

        return result
    
    # After the game ends, all users are detached
    def gameover(self) -> None:
        print("GAME OVER. RESULTS:")
        for user in self.users:
            print("==================================")
            print(self.getuserstate(self.users[user]))
        
        for user in self.users:
            self.users[user].reset()
        self.delete()

    #def __repr__(self) -> str:
    #    for i in self.cells:
    #        print(i)
    #    #for i in self.users:
    #        #print(i) 
