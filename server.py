from socket import *
from threading import Thread, RLock
from multiprocessing import Process, Manager
import sys
import argparse
import board
import user
import auth
import sqlite3


def parsecommand(line: str):
    arglist = line.rstrip('\n').split(' ')
    return arglist

class UserDict:
    def __init__(self) -> None:
        self.mutex = RLock()
        self.data: dict[str, user.User] = {}

    def new(self, username, email, fullname):
        self.mutex.acquire()
        if username not in self.data:
            self.data[username] = user.User(username, email, fullname)
        else:
            pass
        self.mutex.release()

    def list(self):
        self.mutex.acquire()
        res = [name for name in self.data]
        self.mutex.release()
        return res
    
    def isattached(self, username):
        self.mutex.acquire()
        if self.data[username].attachedboard is None:
            res = False
        else:
            res = True
        self.mutex.release()
        return res

class BoardDict:
    def __init__(self) -> None:
        self.mutex = RLock()
        self.data: dict[str, board.Board] = {}

    def new(self, name, file="input.json"):
        self.mutex.acquire()
        if name not in self.data:
            self.data[name] = board.Board(file)
        else:
            pass
        self.mutex.release()

    def list(self):
        self.mutex.acquire()
        res = [name for name in self.data]
        self.mutex.release()
        return res
    
    def open(self, name, username):
        self.mutex.acquire()
        self.data[name].attach(users[username])
        self.mutex.release()

    def close(self, name, username):
        self.mutex.acquire()
        self.data[name].detach(users[username])
        self.mutex.release()

class Agent(Thread):
    class RequestHandler(Thread):
        def __init__(self, sock: socket):
            self.username = None
            self.sock = sock
            Thread.__init__(self)

        def run(self):
            self.connection = sqlite3.connect("userdata.db")
            self.cursor = self.connection.cursor()

            request = self.sock.recv(1024)
            while request != b'':
                cmds = parsecommand(request.decode())
                print(self.username, "commanded", cmds)

                if self.username is None:

                    # login <username> <password>
                    if cmds[0] == "login":
                        if len(cmds) != 3:
                            self.sock.send(f"ERROR: login expects 2 arguments. Received: {len(cmds) - 1}\n".encode())
                        else:
                            self.cursor.execute("SELECT * FROM userdata WHERE username = ?", (cmds[1],))
                            result = self.cursor.fetchone()

                            if result is None:
                                self.sock.send(f"ERROR: User {cmds[1]} not found.\n".encode())
                            elif auth.match(result[2], cmds[2]):
                                self.username = cmds[1]
                                users.new(self.username, result[3], result[4])
                                self.sock.send(f"INFO: Logged in.\n".encode())
                            else:
                                self.sock.send(f"ERROR: Wrong password.\n".encode())

                    # new user <username> <password> <mail> <fullname>
                    elif cmds[0] == "new":
                        if len(cmds) > 1 and cmds[1] == "board":
                            self.sock.send(f"ERROR: Log in to use new board command. You can use new user now.\n".encode())
                        elif len(cmds) > 1 and cmds[1] == "user":
                            if len(cmds) != 6:
                                self.sock.send(f"ERROR: new user expects 4 arguments. Received: {len(cmds) - 2}\n".encode())
                            elif cmds[1] == "user":
                                self.cursor.execute("SELECT * FROM userdata WHERE username = ?", (cmds[2],))
                                result = self.cursor.fetchone()

                                if result is None:
                                    self.cursor.execute("INSERT INTO userdata (username, password, email, fullname) VALUES (? , ?, ?, ?)", (cmds[2], auth.hash(cmds[3]), cmds[4], cmds[5]))
                                    self.connection.commit()
                                    self.sock.send(f"INFO: User created.\n".encode())
                                else:
                                    self.sock.send(f"ERROR: User already exists.\n".encode())
                    
                    else:
                        self.sock.send(f"ERROR: Command not found.\n".encode())

                else:

                    # logout
                    if cmds[0] == "logout":
                        if users.isattached(self.username):
                            self.sock.send(f"ERROR: Detach from the board to logout.\n".encode())
                        else:
                            self.username = None
                            self.sock.send(f"INFO: Logged out.\n".encode())

                    # new board <boardname> <file>
                    elif cmds[0] == "new":
                        if len(cmds) > 1 and cmds[1] == "user":
                            self.sock.send(f"ERROR: Log out to use new user command. You can use new board now.\n".encode())
                        elif len(cmds) > 1 and cmds[1] == "board":
                            if len(cmds) != 3:
                                self.sock.send(f"ERROR: new user expects 1 arguments. Received: {len(cmds) - 2}\n".encode())
                            else:
                                boards.new(cmds[2])
                                self.sock.send(f"INFO: Board created.\n".encode())

                    elif cmds[0] == "list":
                        if len(cmds) != 2:
                            self.sock.send(f"ERROR: list expects 1 arguments. Received: {len(cmds) - 1} \n".encode())
                        else:
                            if cmds[1] == "user":
                                print("\n".join(users.list()))
                            elif cmds[1] == "board":
                                print("\n".join(boards.list()))

                    else:
                        self.sock.send(f"ERROR: Command not found.\n".encode())


                request = self.sock.recv(1024)

    class CallbackHandler(Thread):
        def __init__(self, sock: socket):
            self.sock = sock
            Thread.__init__(self)

        def run(self):
            return

    def __init__(self, sock: socket):
        self.socket = sock
        self.rh = self.RequestHandler(sock)
        self.ch = self.CallbackHandler(sock)
        Thread.__init__(self)

    def run(self):
        self.rh.start()
        self.ch.start()
        self.rh.join()
        self.ch.join()

boards = BoardDict()
users = UserDict()

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=1234, action='store')
args = parser.parse_args()

s = socket(AF_INET, SOCK_STREAM)
s.bind(('', args.port))

s.listen(10)
av = s.accept()

try:
    while av:
        print('accepted: ', av[1])
        a = Agent(av[0])
        a.start()
        av = s.accept()
except KeyboardInterrupt: # Not working
    print("CATCHED")
    s.close()