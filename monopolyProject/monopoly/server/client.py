from collections.abc import Callable, Iterable, Mapping
from socket import *
import argparse
from threading import Thread, RLock, Condition
import json

class Listener(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self) -> None:
        response = s.recv(1024)
        while response != b'':
            print(response.decode())
            response = s.recv(1024)

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=1234, action='store')
args = parser.parse_args()

s = socket(AF_INET, SOCK_STREAM)
s.connect(('', args.port))

cmd = input()

try:
    ls = Listener()
    ls.start()

    while cmd != "quit":
        if cmd != "":
            #cmds = list(filter(None, cmd.split(" ")))
            #if cmds[0] == "new":
            #    print(cmds)
            #    with open(cmds[2], "r") as f:
            #        data = json.load(f)
            #        print(data)
            s.send(cmd.encode())
        cmd = input()
finally:
    s.send("quit".encode()) # Sending quit command to keep server clean
    print("Client shutdown.")
    s.shutdown(SHUT_RDWR)
    s.close()
    ls.join()