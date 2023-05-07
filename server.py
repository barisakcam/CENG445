from socket import *
from threading import Thread, RLock, Condition, Event
import argparse
import board
import user
import auth
import sqlite3
import pprint

class UserAlreadyReady(Exception):
    pass

class UserNotAttached(Exception):
    pass

class NotUsersTurn(Exception):
    pass

def parsecommand(line: str):
    arglist = line.rstrip('\n').split(' ')
    return list(filter(None, arglist))

class UserDict:
    def __init__(self) -> None:
        self.data: dict[str, user.User] = {}

    def __getitem__(self, index) -> user.User:
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
                return True
            else:
                return False # Dont remember why I put this

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
            
    def getmessage(self, username):
        with mutex:
            res = []
            while not users[username].callbackqueue.empty():
                res.append(users[username].callbackqueue.get())
            return "\n".join(res)
        
    def play(self, username, command):
        with mutex:
            if users[username].attachedboard is None:
                raise UserNotAttached
            elif not users[username].status.isplaying:
                raise NotUsersTurn
            else:
                users[username].attachedboard.turn(users[username], command)

class BoardDict:
    def __init__(self) -> None:
        self.data: dict[str, board.Board] = {}

    def __getitem__(self, index):
        return self.data[index]

    def new(self, name, file):
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
            if name in self.data:
                self.data[name].attach(users[username])
                return True
            else:
                return False

    def close(self, username):
        with mutex:
            if users[username].attachedboard is None:
                raise UserNotAttached
            else:
                users[username].attachedboard.detach(users[username])

    def ready(self, username):
        with mutex:
            if users[username].attachedboard is None:
                raise UserNotAttached
            elif users[username].status.ready:
                raise UserAlreadyReady
            else:
                users[username].attachedboard.ready(users[username])

    def notify(self, username): # TODO: Too messy, check with multiple agents
        with mutex:
            for user in users[username].attachedboard.users:
                with users[user].cv:
                    users[user].cv.notify_all()

class Agent(Thread):
    class CallbackHandler(Thread):
        def __init__(self, sock: socket, username: str):
            self.sock = sock
            self.username = username
            self.event = Event()
            Thread.__init__(self)

        def run(self):
            while True:
                with users[self.username].cv:
                    if users[self.username].cv.wait(timeout=0.5):
                        self.sock.send(f"CALLBACK: {users.getmessage(self.username)}\n".encode())
                    else:
                        if self.event.is_set():
                            break

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

            # quit command is sent when a client terminates connection
            # It is used to logout the quiting user to make sure server state remains clean
            if not cmds:
                request = self.sock.recv(1024)
                continue

            if cmds[0] == "quit":
                if self.username is not None:
                    if users.isattached(self.username):
                        boards.close(self.username)

                    self.ch.event.set()
                    self.ch.join()
                
                users.logout(self.username)

                self.username = None

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
                        elif users.islogin(cmds[1]):
                            self.sock.send(f"ERROR: User already logged in.\n".encode())
                        elif auth.match(result[2], cmds[2]):
                            self.username = cmds[1]
                            users.login(self.username, result[3], result[4])
                            self.ch = self.CallbackHandler(self.sock, self.username)
                            self.ch.start()
                            self.sock.send(f"INFO: Logged in.\n".encode())
                        else:
                            self.sock.send(f"ERROR: Wrong password.\n".encode())

                # createuser <username> <password> <mail> <fullname>
                elif cmds[0] == "createuser":
                    if len(cmds) != 5:
                        self.sock.send(f"ERROR: createuser expects 4 arguments. Received: {len(cmds) - 1}\n".encode())
                    else:
                        self.cursor.execute("SELECT * FROM userdata WHERE username = ?", (cmds[1],))
                        result = self.cursor.fetchone()

                        if result is None:
                            self.cursor.execute("INSERT INTO userdata (username, password, email, fullname) VALUES (? , ?, ?, ?)", (cmds[1], auth.hash(cmds[2]), cmds[3], cmds[4]))
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
                        boards.close(self.username)
                        self.sock.send(f"INFO: Closed board.\n".encode())

                    self.ch.event.set()
                    self.ch.join()

                    users.logout(self.username)

                    self.username = None
                    self.sock.send(f"INFO: Logged out.\n".encode())

                # new <boardname> <file>
                elif cmds[0] == "new":
                    if len(cmds) != 3:
                        self.sock.send(f"ERROR: new expects 2 arguments. Received: {len(cmds) - 1}\n".encode())
                    else:
                        try:
                            boards.new(cmds[1], cmds[2])
                            self.sock.send(f"INFO: Board created.\n".encode())
                        except FileNotFoundError:
                            self.sock.send(f"ERROR: Input file not found.\n".encode())

                # list
                elif cmds[0] == "list":
                    if len(cmds) != 1:
                        self.sock.send(f"ERROR: list expects no arguments. Received: {len(cmds) - 1}\n".encode())
                    else:
                        #self.sock.send("\n".join(boards.list()).encode())
                        self.sock.send((boards.list()+"\n").encode())

                # open <boardname> 
                elif cmds[0] == "open":
                    if len(cmds) != 2:
                        self.sock.send(f"ERROR: open expects 1 arguments. Received: {len(cmds) - 1} ".encode())
                    else:
                        if users.isattached(self.username):
                            boards.close(self.username)
                            self.sock.send(f"INFO: Closed board.".encode())

                        if boards.open(cmds[1], self.username):
                            self.sock.send(f"INFO: Opened board {cmds[1]}.".encode())
                        else:
                            self.sock.send(f"ERROR: Board not found.".encode())

                # close
                elif cmds[0] == "close":
                    if len(cmds) != 1:
                        self.sock.send(f"ERROR: open expects no arguments. Received: {len(cmds) - 1}\n".encode())
                    else:
                        try:
                            boards.close(self.username)
                            self.sock.send(f"INFO: Closed board.\n".encode())
                        except UserNotAttached: # TODO: Convert others to exceptions too
                            self.sock.send(f"ERROR: No board is open.\n".encode())

                # ready
                elif cmds[0] == "ready":
                    if len(cmds) != 1:
                        self.sock.send(f"ERROR: ready expects no arguments. Received: {len(cmds) - 1}\n".encode())
                    else:
                        try:
                            boards.ready(self.username)
                            self.sock.send(f"INFO: Ready\n".encode())
                        except UserNotAttached:
                            self.sock.send(f"ERROR: No board is open.\n".encode())
                        except UserAlreadyReady:
                            self.sock.send(f"ERROR: Already ready.\n".encode())

                elif cmds[0] in play_commands:
                    try:
                        users.play(self.username, cmds[0])
                    except UserNotAttached:
                        self.sock.send(f"ERROR: No board is open.\n".encode())
                    except NotUsersTurn:
                        self.sock.send(f"ERROR: Not your turn or game is not started yet.\n".encode())
                    except board.GameCommandNotFound:
                        self.sock.send("ERROR: Game command not found\n".encode())
                    except board.AlreadyRolled:
                        self.sock.send("ERROR: User already rolled\n".encode())
                    except board.NotRolled:
                        self.sock.send("ERROR: User not rolled yet\n".encode())
                    except board.NotProperty:
                        self.sock.send("ERROR: Not a property\n".encode())
                    except board.PropertyOwned:
                        self.sock.send("ERROR: Property is already owned\n".encode())
                    except board.PropertyNotOwned:
                        self.sock.send("ERROR: Property is not owned by user\n".encode())
                    except board.PropertyMaxLevel:
                        self.sock.send("ERROR: Property is already level 5\n".encode())
                    except board.NotEnoughMoney:
                        self.sock.send("ERROR: Not enough money\n".encode())
                    except board.NotJail:
                        self.sock.send("ERROR: Not in jail\n".encode())
                    except board.NotTeleport:
                        self.sock.send("ERROR: Not in teleport\n".encode())
                    except board.InsufficientArguments:
                        self.sock.send("ERROR: There are insufficient arguments for the command\n".encode())
                    except board.MustPick:
                        self.sock.send("ERROR: Must pick a property\n".encode())
                    except board.MustTeleport:
                        self.sock.send("ERROR: Must teleport\n".encode())
                    except board.InvalidTeleport:
                        self.sock.send("ERROR: Teleport is limited to property cells\n".encode())
                    except board.CellIndexError:
                        self.sock.send("ERROR: Given cell index is out of range\n".encode())
                    except board.PropertyOp:
                        self.sock.send("ERROR: Only one property operation can be done in a turn\n".encode())
                    except board.PickError:
                        self.sock.send("ERROR: No need to pick a property\n".encode())

                    boards.notify(self.username)

                else:
                    self.sock.send(f"ERROR: Command not found.\n".encode())      

            request = self.sock.recv(1024)

        print("Agent shutdown.") # For DEBUG


mutex = RLock()
boards = BoardDict()
users = UserDict()
play_commands = ["roll", "end"] # TODO: Adding commands one by one and testing

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