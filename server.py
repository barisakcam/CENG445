from socket import *
from threading import Thread, RLock
from multiprocessing import Process, Manager
import sys
import argparse
import board
import user

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
            self.sock = sock
            Thread.__init__(self)

        def run(self):
            request = self.sock.recv(1024)
            while request != b'':
                print(parsecommand(request.decode()))

                if request[0]:
                    pass

                request = self.sock.recv(1024)

    class CallbackHandler(Thread):
        def __init__(self, sock: socket):
            self.sock = sock
            Thread.__init__(self)

        def run(self):
            while True:
                pass
            request = self.sock.recv(1024)
            while request != b'':
                print("Callback: ", request)
                request = self.sock.recv(1024)

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
