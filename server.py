from socket import *
from threading import Thread, RLock
from multiprocessing import Process, Manager
import sys
import argparse
import board
import user
import auth
import sqlite3


def parsecommand(line: str):         # parse client input provided for convenience
    arglist = line.rstrip('\n').split(' ')
    return arglist

class UserDict:
    def __init__(self) -> None:
        self.mutex = RLock()
        self.data: dict[str, user.User] = {}

    def new(self, username, email, fullname, password):
        self.mutex.acquire()
        if username not in self.data:
            self.data[username] = user.User(username, email, fullname, password)
        else:
            pass
        self.mutex.release()

    def list(self):
        self.mutex.acquire()
        res = [name for name in self.data]
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
            self.logged_in = False
            self.sock = sock
            Thread.__init__(self)

        def run(self):
            self.username = "NOT LOGGED IN USER"
            request = self.sock.recv(1024)
            while request != b'':
                comms = parsecommand(request.decode())
                print(self.username, "commanded", comms)

                if comms[0] == "login" and not self.logged_in:
                    self.sock.send("Username: ".encode())
                    self.username = self.sock.recv(1024).decode()
                    self.username = self.username[:-1] #\n gelmesin diye
                    self.sock.send("Password: ".encode())
                    self.password = self.sock.recv(1024).decode()[:-1]

                    #hashsiz çalışıyor hashli çalışmıyor
                    conn= sqlite3.connect("userdata.db")
                    cur = conn.cursor()
                    cur.execute("SELECT password FROM userdata WHERE username = ?", (self.username,))
                    result = cur.fetchone()
                    if result is not None and auth.match(result[0],self.password):
                        self.sock.send(f"Welcome {self.username}\n".encode())
                        self.logged_in = True
                    else:
                        self.sock.send("Login failed\n".encode())
                        self.username = "NOT LOGGED IN USER"

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

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=1234, action='store')
args = parser.parse_args()

s = socket(AF_INET, SOCK_STREAM)
s.bind(('', args.port))

s.listen(10)
av = s.accept()
boards = BoardDict()
users = UserDict()

try:
    while av:
        print('accepted: ', av[1])
        a = Agent(av[0])
        a.start()
        av = s.accept()
except KeyboardInterrupt: # Not working
    print("CATCHED")
    s.close()