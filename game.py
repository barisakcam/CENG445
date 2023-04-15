from board import Board
from cell import Cell, Property
from user import User
import random

##şimdilik burada kalsın

def roll(board: Board ,user: User):
    move = random.randint(1,6)
    print(user.username, "tossed", move)
    user.status.location_index += move
    user.status.location_index %= len(board.cells)
    print("kaan landed on", board.cells[user.status.location_index].type)
    
    return #bilmiyorum ne döner

def buy(user: User, property: Property):
    if user.status.money >= property.price:

        user.status.money -= property.price
        property.owner = User
        user.status.properties.append(property)

        return True
    return False

def upgrade():
    pass

def pick(property):
    pass

def bail():
    pass

def teleport(newcell):
    pass


b = Board("input.json")
u = User("kaan","k@k","sadfas","12345678")
u.ready()
u.status.start_game(b)
roll(b,u)
roll(b,u)
roll(b,u)

