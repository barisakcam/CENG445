from socket import *
from threading import Thread, RLock, Condition, Event
import argparse
import board
import user
import auth
import sqlite3
import pprint
import json
import websockets
from websockets.sync.server import serve, ServerConnection
from websockets.exceptions import ConnectionClosed

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
        def __init__(self, sock: ServerConnection, username: str):
            self.sock = sock
            self.username = username
            self.event = Event()
            self.gamelog = ["Game logs"]
            Thread.__init__(self)

        def run(self):
            while True:
                with users[self.username].cv:
                    if users[self.username].cv.wait(timeout=0.5):
                        self.gamelog.append(users.getmessage(self.username))
                        continue
                        self.sock.send(users.getmessage(self.username))
                    else:
                        if self.event.is_set():
                            break

    def __init__(self, sock: ServerConnection):
        self.username = None
        self.sock = sock
        self.ch = None
        Thread.__init__(self)

    def run(self):
        self.connection = sqlite3.connect("userdata.db")
        self.cursor = self.connection.cursor()

        try:
            request = self.sock.recv(1024)
            while request != b'':
                cmds = parsecommand(request)
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
                elif cmds[0] == "login":
                    if len(cmds) != 3:
                        self.sock.send(f"ERROR: login expects 2 arguments. Received: {len(cmds) - 1}")
                    else:
                        #self.cursor.execute("SELECT * FROM userdata WHERE username = ?", (cmds[1],))
                        #result = self.cursor.fetchone()

                        if users.islogin(cmds[1]):
                            self.sock.send(f"ERROR: User already logged in.")
                        else:
                            users.login(self.username, "", "")
                            self.ch = self.CallbackHandler(self.sock, self.username)
                            self.ch.start()
                            self.sock.send(f"INFO: Logged in.")

                # createuser <username> <password> <mail> <fullname>
                elif cmds[0] == "createuser":
                    if len(cmds) != 5:
                        self.sock.send(f"ERROR: createuser expects 4 arguments. Received: {len(cmds) - 1}")
                    else:
                        self.cursor.execute("SELECT * FROM userdata WHERE username = ?", (cmds[1],))
                        result = self.cursor.fetchone()

                        if result is None:
                            self.cursor.execute("INSERT INTO userdata (username, password, email, fullname) VALUES (? , ?, ?, ?)", (cmds[1], auth.hash(cmds[2]), cmds[3], cmds[4]))
                            self.connection.commit()
                            self.sock.send(f"INFO: User created.")
                        else:
                            self.sock.send(f"ERROR: User already exists.")

                # logout
                elif cmds[0] == "logout":
                    if users.islogin(self.username):
                        if users.isattached(self.username):
                            boards.close(self.username)
                            self.sock.send(f"INFO: Closed board.")

                        self.ch.event.set()
                        self.ch.join()

                        users.logout(self.username)

                    self.username = None
                    self.sock.send(f"INFO: Logged out.")

                # new <boardname> <file>
                elif cmds[0] == "new":
                    if len(cmds) != 3:
                        self.sock.send(f"ERROR: new expects 2 arguments. Received: {len(cmds) - 1}")
                    else:
                        try:
                            boards.new(cmds[1], cmds[2])
                            self.sock.send(f"INFO: Board created.")
                        except FileNotFoundError:
                            self.sock.send(f"ERROR: Input file not found.")

                # list
                elif cmds[0] == "list":
                    if len(cmds) != 1:
                        self.sock.send(f"ERROR: list expects no arguments. Received: {len(cmds) - 1} ")
                    else:
                        #self.sock.send("\n".join(boards.list()))
                        self.sock.send(boards.list())

                # open <boardname> 
                elif cmds[0] == "open":
                    if len(cmds) != 2:
                        self.sock.send(f"ERROR: open expects 1 arguments. Received: {len(cmds) - 1} ")
                    else:
                        if users.isattached(self.username):
                            boards.close(self.username)
                            self.sock.send(f"INFO: Closed board.")

                        if boards.open(cmds[1], self.username):
                            self.sock.send(f"INFO: Opened board {cmds[1]}.")
                        else:
                            self.sock.send(f"ERROR: Board not found.")

                # close
                elif cmds[0] == "close":
                    if len(cmds) != 1:
                        self.sock.send(f"ERROR: open expects no arguments. Received: {len(cmds) - 1} ")
                    else:
                        try:
                            boards.close(self.username)
                            self.sock.send(f"INFO: Closed board.")
                        except UserNotAttached: # TODO: Convert others to exceptions too
                            self.sock.send(f"ERROR: No board is open.")

                # ready
                elif cmds[0] == "ready":
                    if len(cmds) != 1:
                        self.sock.send(f"ERROR: ready expects no arguments. Received: {len(cmds) - 1} ")
                    else:
                        try:
                            boards.ready(self.username)
                            self.sock.send(f"INFO: Ready")
                            boards.notify(self.username)
                        except UserNotAttached:
                            self.sock.send(f"ERROR: No board is open.")
                        except UserAlreadyReady:
                            self.sock.send(f"ERROR: Already ready.")
                        except UserIsSpectator:
                            self.sock.send(f"ERROR: You are a spectator.")

                # <playcommand> [newcell | pick]
                elif cmds[0] in play_commands:
                    try:
                        if cmds[0] == "teleport":
                            if len(cmds) != 2:
                                self.sock.send(f"ERROR: teleport expects 1 argument. Received: {len(cmds) - 1} ")
                            else:
                                if not cmds[1].isdigit():
                                    self.sock.send("ERROR: teleport argument must be an integer index")
                                else:
                                    users.play(self.username, cmds[0], newcell=cmds[1])
                                    self.sock.send("SUCCESS")
                        elif cmds[0] == "pick":
                            if len(cmds) != 2:
                                self.sock.send(f"ERROR: pick expects 1 argument. Received: {len(cmds) - 1} ")
                            else:
                                if not cmds[1].isdigit():
                                    self.sock.send("ERROR: pick argument must be an integer index")
                                else:
                                    users.play(self.username, cmds[0], pick=cmds[1])
                                    self.sock.send("SUCCESS")
                        else:
                            if len(cmds) != 1:
                                self.sock.send(f"ERROR: {cmds[0]} expects no argument. Received: {len(cmds) - 1} ")
                            else:
                                users.play(self.username, cmds[0])
                                self.sock.send("SUCCESS")
                                #with users[self.username].cv:
                                #    self.sock.send(users.getmessage(self.username))
                        
                        boards.notify(self.username)
                    except UserNotAttached:
                        self.sock.send(f"ERROR: No board is open.")
                    except NotUsersTurn:
                        self.sock.send(f"ERROR: Not your turn or game is not started yet.")
                    except board.GameCommandNotFound:
                        self.sock.send("ERROR: Game command not found")
                    except board.AlreadyRolled:
                        self.sock.send("ERROR: User already rolled")
                    except board.NotRolled:
                        self.sock.send("ERROR: User not rolled yet")
                    except board.NotProperty:
                        self.sock.send("ERROR: Not a property")
                    except board.PropertyOwned:
                        self.sock.send("ERROR: Property is already owned")
                    except board.PropertyNotOwned:
                        self.sock.send("ERROR: Property is not owned by user")
                    except board.PropertyMaxLevel:
                        self.sock.send("ERROR: Property is already level 5")
                    except board.NotEnoughMoney:
                        self.sock.send("ERROR: Not enough money")
                    except board.NotJail:
                        self.sock.send("ERROR: Not in jail")
                    except board.NotTeleport:
                        self.sock.send("ERROR: Not in teleport")
                    except board.InsufficientArguments:
                        self.sock.send("ERROR: There are insufficient arguments for the command")
                    except board.MustPick:
                        self.sock.send("ERROR: Must pick a property")
                    except board.MustTeleport:
                        self.sock.send("ERROR: Must teleport")
                    except board.InvalidTeleport:
                        self.sock.send("ERROR: Teleport is limited to property cells")
                    except board.CellIndexError:
                        self.sock.send("ERROR: Given cell index is out of range")
                    except board.PropertyOp:
                        self.sock.send("ERROR: Only one property operation can be done in a turn")
                    except board.PickError:
                        self.sock.send("ERROR: No need to pick a property")

                # userinfo <username>
                elif cmds[0] == "userinfo":
                    try:
                        self.sock.send(users.getstatus(cmds[1]))
                    except UserDoesNotExist:
                        self.sock.send("ERROR: User does not exist.")
                    except IndexError:
                        self.sock.send("ERROR: User name is expected.")

                # boardinfo <boardname>
                elif cmds[0] == "boardinfo":
                    try:
                        self.sock.send(boards.getstatus(cmds[1]))
                    except BoardDoesNotExist:
                        self.sock.send("ERROR: Board does not exist.")
                    except IndexError:
                        self.sock.send("ERROR: Board name is expected.")

                # gamelog
                elif cmds[0] == "gamelog":
                    if self.ch is not None:
                        self.sock.send("\n".join(self.ch.gamelog))
                        print("\n".join(self.ch.gamelog))
                    else:
                        self.ch = self.CallbackHandler(self.sock, self.username) # Django server reset fix
                        self.ch.start()
                        self.sock.send("\n".join(self.ch.gamelog))
                        print("\n".join(self.ch.gamelog))

                else:
                    self.sock.send(f"ERROR: Command not found.")      

                request = self.sock.recv(1024)

        except ConnectionClosed as e:
            print(e)
       
        print("Agent shutdown.") # For DEBUG


mutex = RLock()
boards = BoardDict()
users = UserDict()
play_commands = ["roll", "buy", "upgrade", "teleport", "pick", "bail", "end"] # TODO: Adding commands one by one and testing

def ws_handler(websocket: ServerConnection):
    print("received")
    #websocket.send("test")
    #try:
    #    inp = websocket.recv(1024)
    #    while inp:
    #        print(inp)
    #        inp = websocket.recv(1024)
    #except ConnectionClosed as e:
    #    print(e)
    
    a = Agent(websocket)
    a.start()
    a.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=1234, action='store')
    args = parser.parse_args()

    #s = socket(AF_INET, SOCK_STREAM)
    #s.bind(('', args.port))
#
    #s.listen(10)
    #av = s.accept()
#
    #try:
    #    while av:
    #        print('accepted: ', av[1])
    #        a = Agent(av[0])
    #        a.start()
    #        av = s.accept()
    #except KeyboardInterrupt: # Not working when there are active connections
    #    print("Server shutdown.")
    #    s.shutdown(SHUT_RDWR)
    #    s.close()

    HOST = ''
    PORT = int(args.port)

    with serve(ws_handler , host = HOST, port = PORT) as server:
        print("serving")
        server.serve_forever()
