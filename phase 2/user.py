import auth
import pprint
import board
import queue
import threading

class UserNotAttached(Exception):
    pass

class UserStatus: #userın oyundaki değerlerini tutuyor
    
    def __init__(self) -> None:
        self.constructor()

    def constructor(self):
        self.ready = False #ready olunca Truelanacak
        self.properties = [] #hiçbir şeyi yok daha
        self.location_index = None
        self.money = 0 #oyun başlayınca board.startup olacak
        self.isplaying = False #True when its user's turn
        self.rolled = False #True after roll commands
        self.picked_cell = None
        self.jail = False
        self.jailcards = 0
        self.paidteleport = False
        self.freeteleport = False
        self.pick = None
        self.propertyop = False
        self.isspectator = False

    def reset(self):
        self.ready = False #ready olunca Truelanacak
        self.properties.clear()
        self.location_index = None
        self.money = 0 #oyun başlayınca board.startup olacak
        self.isplaying = False #True when its user's turn
        self.rolled = False #True after roll commands
        self.picked_cell = None
        self.jail = False
        self.jailcards = 0
        self.paidteleport = False
        self.freeteleport = False
        self.pick = None
        self.propertyop = False
        self.isspectator = False

    def start_game(self,board):
        self.location_index = 0
        self.money = board.startup #oyun başlayınca board.startup olacak
    
class User:

    def __init__(self, username: str, email: str, fullname: str) -> None:
        self.constructor(username, email, fullname)

    def __del__(self) -> None:
        self.delete()
        
    def constructor(self, username: str, email: str, fullname: str) -> None:
        self.username = username
        self.email = email
        self.fullname = fullname
        ##############################
        self.status = UserStatus()
        self.attachedboard: board.Board = None

        self.callbackqueue = queue.Queue()
        self.cvlock = threading.Lock()
        self.cv = threading.Condition(self.cvlock)

    def reset(self) -> None:
        self.status.reset()
        self.attachedboard = None

    def get(self) -> str:
        return pprint.pformat({"username": self.username, \
                               "email": self.email, \
                               "fullname": self.fullname})
    
    def getstatus(self) -> dict:
        return {"username": self.username, \
                "properties": [prop.get() for prop in self.status.properties], \
                "location": self.status.location_index, \
                "money": self.status.money,
                "ready": self.status.ready,
                "isplaying": self.status.isplaying}
    
    def ready(self):
        if self.attachedboard is not None:
            self.status.ready = True
        else:
            raise UserNotAttached
    
    # Used kwargs to allow partial updates
    def update(self, **kwargs) -> None:
        if "username" in kwargs:
            self.username = kwargs["username"]

        if "email" in kwargs:
            self.email = kwargs["email"]

        if "fullname" in kwargs:
            self.fullname = kwargs["fullname"]

        if "passwd" in kwargs:
            self.passwd = kwargs["passwd"]

    def delete(self) -> None:
        pass

    def auth(self, plainpass: str) -> bool:
        return auth.match(self.passwd, plainpass)
    
    def login(self) -> None:
        """PART2"""
        pass

    def checksession(self, token: str) -> bool:
        """PART2"""
        pass

    def logout(self) -> None:
        """PART2"""
        pass

    def callback(self, message: str) -> None:
        with self.cv:
            self.callbackqueue.put(f"CALLBACK: {message}")
        print(f"{self.username} received callback:")
        print(message)

    def turncb(self, message: str) -> None:
        with self.cv:
            self.callbackqueue.put(f"TURNCB: {message}")
        print(f"{self.username} received turncb:")
        print(message)

    def __repr__(self):
        return self.username






    