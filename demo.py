import board
import user
import cmd

class DemoShell(cmd.Cmd):
    intro = "Online Monopoly Game Platform"
    prompt = "(monopoly) "
    file = None

    boards = {}
    users = {}
    
    def do_add_user(self, args: str):
        arg_list = args.split()

        if len(arg_list) == 4:
            if arg_list[0] in self.users:
                print("ERROR: User exists.")
            else:
                self.users[arg_list[0]] = user.User(arg_list[0], arg_list[1], arg_list[2], arg_list[3])

        else:
            print(f"Wrong number of arguments: 4 expected, {len(arg_list)} received")

    def do_ls_user(self, args: str):
        for key in self.users.keys():
            print(key)

    def do_info_user(self, args: str):
        arg_list = args.split()

        if len(arg_list) == 1:
            if arg_list[0] in self.users:
                print(self.users[arg_list[0]].get())
            else:
                print("ERROR: User does not exist")
        else:
            print(f"Wrong number of arguments: 1 expected, {len(arg_list)} received")

    def do_info_user_status(self, args: str):
        arg_list = args.split()

        if len(arg_list) == 1:
            if arg_list[0] in self.users:
                if self.users[arg_list[0]].attachedboard is not None:
                    print(self.users[arg_list[0]].attachedboard.getuserstate(self.users[arg_list[0]]))
                else:
                    print("ERROR: User is not attached to a board")
            else:
                print("ERROR: User does not exist")
        else:
            print(f"Wrong number of arguments: 1 expected, {len(arg_list)} received")

    def do_add_board(self, args: str):
        arg_list = args.split()

        if len(arg_list) == 2:
            if arg_list[0] in self.boards:
                print("ERROR: Board exists")
            else:
                try:
                    self.boards[arg_list[0]] = board.Board(arg_list[1])
                except FileNotFoundError:
                    print("ERROR: File not found")

        else:
            print(f"Wrong number of arguments: 2 expected, {len(arg_list)} received")

    def do_ls_board(self, args: str):
        for key in self.boards.keys():
            print(key)

    def do_info_board(self, args: str):
        arg_list = args.split()

        if len(arg_list) == 1:
            if arg_list[0] in self.boards:
                print(self.boards[arg_list[0]].getboardstate())
            else:
                print("ERROR: Board does not exist")
        else:
            print(f"Wrong number of arguments: 1 expected, {len(arg_list)} received")

    def do_attach_user(self, args: str):
        arg_list = args.split()

        if len(arg_list) == 2:
            if arg_list[0] in self.boards:
                if arg_list[1] in self.users:
                    try:
                        self.boards[arg_list[0]].attach(self.users[arg_list[1]])
                    except board.UserExists:
                        print("ERROR: User already attached")
                    except board.GameAlreadyStarted:
                        print("ERROR: Game is already started")
                else:
                    print("ERROR: User does not exist")
            else:
                print("ERROR: Board does not exist")
        else:
            print(f"Wrong number of arguments: 2 expected, {len(arg_list)} received")

    def do_detach_user(self, args: str):
        arg_list = args.split()

        if len(arg_list) == 2:
            if arg_list[0] in self.boards:
                if arg_list[1] in self.users:
                    try:
                        self.boards[arg_list[0]].detach(self.users[arg_list[1]])
                    except board.UserNotFound:
                        print("ERROR: User is not attached")
                else:
                    print("ERROR: User does not exist")
            else:
                print("ERROR: Board does not exist")
        else:
            print(f"Wrong number of arguments: 2 expected, {len(arg_list)} received")

    def do_ready(self, args: str):
        arg_list = args.split()

        if len(arg_list) == 1:
            if arg_list[0] in self.users:
                try:
                    self.users[arg_list[0]].attachedboard.ready(self.users[arg_list[0]])
                except user.UserNotAttached:
                    print("ERROR: User is not attached to a board")
            else:
                print("ERROR: User does not exist")
        else:
            print(f"Wrong number of arguments: 1 expected, {len(arg_list)} received")

    def do_play(self, args: str):
        arg_list = args.split()

        if len(arg_list) == 2 or len(arg_list) == 3:
            if arg_list[0] in self.users:
                if self.users[arg_list[0]].attachedboard is not None:
                    if self.users[arg_list[0]].status.isplaying:
                        try:
                            if arg_list[1] == "teleport":
                                if len(arg_list) == 2:
                                    print("ERROR: Missing transport argument")
                                else:
                                    self.users[arg_list[0]].attachedboard.turn(self.users[arg_list[0]], arg_list[1], newcell=arg_list[2])
                            elif arg_list[1] == "pick":
                                if len(arg_list) == 2:
                                    print("ERROR: Missing pick argument")
                                else:
                                    self.users[arg_list[0]].attachedboard.turn(self.users[arg_list[0]], arg_list[1], pick=arg_list[2])
                            else:
                                self.users[arg_list[0]].attachedboard.turn(self.users[arg_list[0]], arg_list[1])
                        except board.GameCommandNotFound:
                            print("ERROR: Game command not found") #TODO: Catch wrong commands
                        except board.AlreadyRolled:
                            print("ERROR: User already rolled")
                        except board.NotRolled:
                            print("ERROR: User not rolled yet")
                        except board.NotProperty:
                            print("ERROR: Not a property")
                        except board.PropertyOwned:
                            print("ERROR: Property is already owned")
                        except board.PropertyNotOwned:
                            print("ERROR: Property is not owned by user")
                        except board.PropertyMaxLevel:
                            print("ERROR: Property is already level 5")
                        except board.NotEnoughMoney:
                            print("ERROR: Not enough money")
                        except board.NotJail:
                            print("ERROR: Not in jail")
                        except board.NotTeleport:
                            print("ERROR: Not in teleport")
                        except board.InsufficientArguments:
                            print("ERROR: There are insufficient arguments for the command")
                        except board.MustPick:
                            print("ERROR: Must pick a property")
                        except board.MustTeleport:
                            print("ERROR: Must teleport")
                        except board.InvalidTeleport:
                            print("ERROR: Teleport is limited to property cells")
                        except board.CellIndexError:
                            print("ERROR: Given cell index is out of range")
                        except board.PropertyOp:
                            print("ERROR: Only one property operation can be done in a turn")
                    else:
                        print("ERROR: Not user's turn")
                else:
                    print("ERROR: User is not attached to a board")
            else:
                print("ERROR: User does not exist")
        else:
            print(f"Wrong number of arguments: 2 or 3 expected, {len(arg_list)} received")

    #######################################################

    def do_playback(self, arg):
        'Playback commands from a file:  PLAYBACK rose.cmd'
        self.close()
        with open(arg) as f:
            self.cmdqueue.extend(f.read().splitlines())

    def do_quit(self, args: str):
        return True

    def default(self, line: str) -> None:
        print(f"Command \'{line.split()[0]}\' not found.")
        return None
    
    def emptyline(self) -> bool:
        return False
    
    def close(self):
        if self.file:
            self.file.close()
            self.file = None
        
if __name__ == "__main__":
    ds = DemoShell()
    ds.cmdloop()