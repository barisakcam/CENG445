# CENG445 #
Online Monopoly

Barış Akçam - 2448041
Kaan Göçmen - 2414894

# ====== PHASE 1 ====== #
auth.py: Hashing functions used to encrypt user passwords
board.py: Board class with exceptions to deal with bad user actions
cell.py: Cell class
demo.py: Demo console application written with cmd library, some of the CRUD functionality is implemented here since objects can not delete themselves in python.
user.py: User class

*.json: Example board inputs
test_cmds.txt: Example commands

# ====== PHASE 2 ====== #
server.py: TCP server application. Handles TCP requests and creates threads handling them.
client.py: TCP client application. User connect to server using client application.

demo.py is no longer used