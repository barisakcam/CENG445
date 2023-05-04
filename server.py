from socket import *
from threading import Thread
from multiprocessing import Process
import sys
import argparse

class Agent(Process):
    def __init__(self, sock: socket):
        self.sock = sock
        Process.__init__(self)

    def run(self):
        request = self.sock.recv(1024)
        while request != '':
            print(request)
            request = self.sock.recv(1024)

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=1234, action='store')
args = parser.parse_args()

s = socket(AF_INET, SOCK_STREAM)
s.bind(('', args.port))

s.listen(10)
av = s.accept()
while av:
    print('accepted: ', av[1])
    a = Agent(av[0])
    a.start()
    av = s.accept()