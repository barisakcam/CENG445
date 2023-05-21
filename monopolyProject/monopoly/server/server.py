from socket import *
from threading import Thread, RLock, Condition, Event
import argparse
import board
import user
import auth
import sqlite3
import pprint
import json

class UserAlreadyReady(Exception):
    pass

class UserNotAttached(Exception):
    pass

class NotUsersTurn(Exception):
    pass

class UserIsSpectator(Exception):
    pass

class UserDoesNotExist(Exception):
    pass

class BoardDoesNotExist(Exception):
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
            while not self.data[username].callbackqueue.empty():
                res.append(f"{self.data[username].callbackqueue.get()}")
            return "\n".join(res)
        
    def play(self, username, command, newcell=None, pick=None):
        with mutex:
            if self.data[username].attachedboard is None:
                raise UserNotAttached
            elif not self.data[username].status.isplaying:
                raise NotUsersTurn
            else:
                if command == "teleport":
                    self.data[username].attachedboard.turn(self.data[username], command, newcell=newcell)
                elif command == "pick":
                    self.data[username].attachedboard.turn(self.data[username], command, pick=pick)
                else:
                    self.data[username].attachedboard.turn(self.data[username], command)

    def getstatus(self, username):
        with mutex:
            if username in self.data:
                return pprint.pformat(self.data[username].getstatus())
            else:
                raise UserDoesNotExist

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
            res = [{"boardname": name, 
                    "users": [user for user in self.data[name].users], 
                    "spectators": [spectator for spectator in self.data[name].spectators],
                    "gamestarted": self.data[name].gamestarted} for name in self.data]
        return json.dumps(res)
    
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
            elif users[username].status.isspectator:
                raise UserIsSpectator
            else:
                users[username].attachedboard.ready(users[username])

    def notify(self, username): # TODO: Too messy, check with multiple agents
        with mutex:
            for user in users[username].attachedboard.users:
                with users[user].cv:
                    users[user].cv.notify_all()
            for spec in users[username].attachedboard.spectators:
                with users[spec].cv:
                    users[spec].cv.notify_all()

    def getstatus(self, boardname):
        with mutex:
            if boardname in self.data:
                return self.data[boardname].getboardstate()
            else:
                raise BoardDoesNotExist

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
                        self.sock.send(users.getmessage(self.username).encode())
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
            self.username = cmds[0]
            cmds = cmds[1:]
            print(self.username, "commanded", cmds)

            # quit command is sent when a client terminates connection
            # It is used to logout the quiting user to make sure server state remains clean
            if cmds[0] == "quit":
                if self.username is not None:
                    if users.isattached(self.username):
                        boards.close(self.username)

                    self.ch.event.set()
                    self.ch.join()
                
                users.logout(self.username)

                self.username = None

            # login <username> <password>
            if cmds[0] == "login":
                if len(cmds) != 3:
                    self.sock.send(f"ERROR: login expects 2 arguments. Received: {len(cmds) - 1}".encode())
                else:
                    #self.cursor.execute("SELECT * FROM userdata WHERE username = ?", (cmds[1],))
                    #result = self.cursor.fetchone()

                    if users.islogin(cmds[1]):
                        self.sock.send(f"ERROR: User already logged in.".encode())
                    else:
                        users.login(self.username, "", "")
                        self.ch = self.CallbackHandler(self.sock, self.username)
                        self.ch.start()
                        self.sock.send(f"INFO: Logged in.".encode())

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

            # logout
            elif cmds[0] == "logout":
                if users.isattached(self.username):
                    boards.close(self.username)
                    self.sock.send(f"INFO: Closed board.".encode())

                self.ch.event.set()
                self.ch.join()

                users.logout(self.username)

                self.username = None
                self.sock.send(f"INFO: Logged out.".encode())

            # new <boardname> <file>
            elif cmds[0] == "new":
                if len(cmds) != 3:
                    self.sock.send(f"ERROR: new expects 2 arguments. Received: {len(cmds) - 1}".encode())
                else:
                    try:
                        boards.new(cmds[1], cmds[2])
                        self.sock.send(f"INFO: Board created.".encode())
                    except FileNotFoundError:
                        self.sock.send(f"ERROR: Input file not found.".encode())

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
                        self.sock.send(f"INFO: Closed board.".encode())

                    if boards.open(cmds[1], self.username):
                        self.sock.send(f"INFO: Opened board {cmds[1]}.".encode())
                    else:
                        self.sock.send(f"ERROR: Board not found.".encode())

            # close
            elif cmds[0] == "close":
                if len(cmds) != 1:
                    self.sock.send(f"ERROR: open expects no arguments. Received: {len(cmds) - 1} ".encode())
                else:
                    try:
                        boards.close(self.username)
                        self.sock.send(f"INFO: Closed board.".encode())
                    except UserNotAttached: # TODO: Convert others to exceptions too
                        self.sock.send(f"ERROR: No board is open.".encode())

            # ready
            elif cmds[0] == "ready":
                if len(cmds) != 1:
                    self.sock.send(f"ERROR: ready expects no arguments. Received: {len(cmds) - 1} ".encode())
                else:
                    try:
                        boards.ready(self.username)
                        self.sock.send(f"INFO: Ready".encode())
                        boards.notify(self.username)
                    except UserNotAttached:
                        self.sock.send(f"ERROR: No board is open.".encode())
                    except UserAlreadyReady:
                        self.sock.send(f"ERROR: Already ready.".encode())
                    except UserIsSpectator:
                        self.sock.send(f"ERROR: You are a spectator.".encode())

            # <playcommand> [newcell | pick]
            elif cmds[0] in play_commands:
                try:
                    if cmds[0] == "teleport":
                        if len(cmds) != 2:
                            self.sock.send(f"ERROR: teleport expects 1 argument. Received: {len(cmds) - 1} ".encode())
                        else:
                            if not cmds[1].isdigit():
                                self.sock.send("ERROR: teleport argument must be an integer index".encode())
                            else:
                                users.play(self.username, cmds[0], newcell=cmds[1])
                    elif cmds[0] == "pick":
                        if len(cmds) != 2:
                            self.sock.send(f"ERROR: pick expects 1 argument. Received: {len(cmds) - 1} ".encode())
                        else:
                            if not cmds[1].isdigit():
                                self.sock.send("ERROR: pick argument must be an integer index".encode())
                            else:
                                users.play(self.username, cmds[0], pick=cmds[1])
                    else:
                        if len(cmds) != 1:
                            self.sock.send(f"ERROR: {cmds[0]} expects no argument. Received: {len(cmds) - 1} ".encode())
                        else:
                            users.play(self.username, cmds[0])
                    
                    boards.notify(self.username)
                except UserNotAttached:
                    self.sock.send(f"ERROR: No board is open.".encode())
                except NotUsersTurn:
                    self.sock.send(f"ERROR: Not your turn or game is not started yet.".encode())
                except board.GameCommandNotFound:
                    self.sock.send("ERROR: Game command not found".encode())
                except board.AlreadyRolled:
                    self.sock.send("ERROR: User already rolled".encode())
                except board.NotRolled:
                    self.sock.send("ERROR: User not rolled yet".encode())
                except board.NotProperty:
                    self.sock.send("ERROR: Not a property".encode())
                except board.PropertyOwned:
                    self.sock.send("ERROR: Property is already owned".encode())
                except board.PropertyNotOwned:
                    self.sock.send("ERROR: Property is not owned by user".encode())
                except board.PropertyMaxLevel:
                    self.sock.send("ERROR: Property is already level 5".encode())
                except board.NotEnoughMoney:
                    self.sock.send("ERROR: Not enough money".encode())
                except board.NotJail:
                    self.sock.send("ERROR: Not in jail".encode())
                except board.NotTeleport:
                    self.sock.send("ERROR: Not in teleport".encode())
                except board.InsufficientArguments:
                    self.sock.send("ERROR: There are insufficient arguments for the command".encode())
                except board.MustPick:
                    self.sock.send("ERROR: Must pick a property".encode())
                except board.MustTeleport:
                    self.sock.send("ERROR: Must teleport".encode())
                except board.InvalidTeleport:
                    self.sock.send("ERROR: Teleport is limited to property cells".encode())
                except board.CellIndexError:
                    self.sock.send("ERROR: Given cell index is out of range".encode())
                except board.PropertyOp:
                    self.sock.send("ERROR: Only one property operation can be done in a turn".encode())
                except board.PickError:
                    self.sock.send("ERROR: No need to pick a property".encode())

            # userinfo <username>
            elif cmds[0] == "userinfo":
                try:
                    self.sock.send(users.getstatus(cmds[1]).encode())
                except UserDoesNotExist:
                    self.sock.send("ERROR: User does not exist.".encode())
                except IndexError:
                    self.sock.send("ERROR: User name is expected.".encode())

            # boardinfo <boardname>
            elif cmds[0] == "boardinfo":
                try:
                    self.sock.send(boards.getstatus(cmds[1]).encode())
                except BoardDoesNotExist:
                    self.sock.send("ERROR: Board does not exist.".encode())
                except IndexError:
                    self.sock.send("ERROR: Board name is expected.".encode())

            else:
                self.sock.send(f"ERROR: Command not found.".encode())      

            request = self.sock.recv(1024)

        print("Agent shutdown.") # For DEBUG


mutex = RLock()
boards = BoardDict()
users = UserDict()
play_commands = ["roll", "buy", "upgrade", "teleport", "pick", "bail", "end"] # TODO: Adding commands one by one and testing

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