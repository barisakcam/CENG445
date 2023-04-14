import auth


class UserStatus: #userın oyundaki değerlerini tutuyor
    
    def __init__() -> None:
       self.constructor()

    def constructor(self):
       self.ready = False #ready olunca Truelanacak
       self.properties = [] #hiçbir şeyi yok daha
       self.location_index = None #oyun başlayınca board.cells[0] olacak
       self.money = 0 #oyun başlayınca board.startup olacak

class User:

    def __init__(self, username: str, email: str, fullname: str, passwd: str) -> None:
        self.constructor(username, email, fullname, passwd)

    def __del__(self) -> None:
        self.delete()
        
    def constructor(self, username: str, email: str, fullname: str, passwd: str) -> None:
        self.username = username
        self.email = email
        self.fullname = fullname
        self.passwd = auth.hash(passwd)
        ##############################
        self.status = UserStatus()
    def get(self) -> str:
        return str({"username": self.username, \
                    "email": self.email, \
                    "fullname": self.fullname, \
                    "passwd": self.passwd})
    
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
        """PART2 (I GUESS)"""
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





    