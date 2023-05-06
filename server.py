from socket import *
from threading import Thread, RLock
import argparse
import board
import user
import auth
import sqlite3
import pprint

def parsecommand(line: str):
    arglist = line.rstrip('\n').split(' ')
    return arglist

class UserDict:
    def __init__(self) -> None:
        self.data: dict[str, user.User] = {}

    def __getitem__(self, index):
        return self.data[index]
    
    def login(self, username, email, fullname):
        with mutex:
            if username not in self.data:
                self.data[username] = user.User(username, email, fullname)
            else:
                pass

    def logout(self, username):
        with mutex:
            if username in self.data:
                del self.data[username]
            else:
                return False

    def list(self):
        with mutex:
            res = [name for name in self.data]
        return res
    
    def isattached(self, username):
        with mutex:
            if self.data[username].attachedboard is None:
                res = False
            else:
                res = True
        return res

    def islogin(self, username):
        with mutex:
            if username in self.data:
                return True
            else:
                return False

class BoardDict:
    def __init__(self) -> None:
        self.data: dict[str, board.Board] = {}

    def __getitem__(self, index):
        return self.data[index]

    def new(self, name, file="input.json"):
        with mutex:
            if name not in self.data:
                self.data[name] = board.Board(file)
            else:
                pass

    def list(self):
        with mutex:
            res = [{"boardname": name, "users": [user for user in self.data[name].users]} for name in self.data]
        return pprint.pformat(res)
    
    def open(self, name, username):
        with mutex:
            self.data[name].attach(users[username])

    def close(self, username):
        with mutex:
            users[username].attachedboard.detach(users[username])

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
                            self.sock.send(f"ERROR: login expects 2 arguments. Received: {len(cmds) - 1}".encode())
                        else:
                            self.cursor.execute("SELECT * FROM userdata WHERE username = ?", (cmds[1],))
                            result = self.cursor.fetchone()

                            if result is None:
                                self.sock.send(f"ERROR: User {cmds[1]} not found.".encode())
                            elif users.islogin(cmds[1]):
                                self.sock.send(f"ERROR: User already logged in.".encode())
                            elif auth.match(result[2], cmds[2]):
                                self.username = cmds[1]
                                users.login(self.username, result[3], result[4])
                                self.sock.send(f"INFO: Logged in.".encode())
                            else:
                                self.sock.send(f"ERROR: Wrong password.".encode())

                    # createuser <username> <password> <mail> <fullname>
                    elif cmds[0] == "createuser":
                        if len(cmds) != 5:
                            self.sock.send(f"ERROR: createuser expects 4 arguments. Received: {len(cmds) - 1}".encode())
                        else:
                            self.cursor.execute("SELECT * FROM userdata WHERE username = ?", (cmds[1],))
                            result = self.cursor.fetchone()

                            if result is None:
                                self.cursor.execute("INSERT INTO userdata (username, password, email, fullname) VALUES (? , ?, ?, ?)", (cmds[1], auth.hash(cmds[2]), cmds[3], cmds[4]))
                                self.connection.commit()
                                self.sock.send(f"INFO: User created.".encode())
                            else:
                                self.sock.send(f"ERROR: User already exists.".encode())
                    
                    else:
                        self.sock.send(f"ERROR: Command not found.".encode())

                else:

                    # logout
                    if cmds[0] == "logout":
                        if users.isattached(self.username):
                            self.sock.send(f"ERROR: Detach from the board to logout.".encode())
                        else:
                            self.username = None
                            self.sock.send(f"INFO: Logged out.".encode())

                    # new <boardname> <file>?NOTADDED
                    elif cmds[0] == "new":
                        if len(cmds) != 2:
                            self.sock.send(f"ERROR: new expects 1 arguments. Received: {len(cmds) - 1}".encode())
                        else:
                            boards.new(cmds[1])
                            self.sock.send(f"INFO: Board created.".encode())

                    # list
                    elif cmds[0] == "list":
                        if len(cmds) != 1:
                            self.sock.send(f"ERROR: list expects no arguments. Received: {len(cmds) - 1} ".encode())
                        else:
                            #self.sock.send("\n".join(boards.list()).encode())
                            self.sock.send(boards.list().encode())

                    # open <boardname> 
                    elif cmds[0] == "open":
                        if len(cmds) != 2:
                            self.sock.send(f"ERROR: open expects 1 arguments. Received: {len(cmds) - 1} ".encode())
                        else:
                            if users.isattached(self.username):
                                boards.close(self.username)
                            
                            boards.open(cmds[1], self.username)
                            self.sock.send(f"INFO: Opened board {cmds[1]}".encode())

                    # close
                    elif cmds[0] == "close":
                        if len(cmds) != 1:
                            self.sock.send(f"ERROR: open expects no arguments. Received: {len(cmds) - 1} ".encode())
                        else:
                            boards.close(self.username)
                            self.sock.send(f"INFO: Opened board {cmds[1]}".encode())

                    else:
                        self.sock.send(f"ERROR: Command not found.".encode())
                    

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

mutex = RLock()
boards = BoardDict()
users = UserDict()

if __name__ == "__main__":
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
    except KeyboardInterrupt: # Not working when there are active connections
        print("Server shutdown.")
        s.shutdown(SHUT_RDWR)
        s.close()