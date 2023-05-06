from socket import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=1234, action='store')
args = parser.parse_args()

s = socket(AF_INET, SOCK_STREAM)
s.connect(('', args.port))

print("$ ", end='')
cmd = input()

try:
    while cmd != "quit":
        if cmd != "":
            s.send(cmd.encode())
            response = s.recv(1024) ### EACH REQUEST MUST HAVE A RESPONSE ###
            print(response.decode())
        print("$ ", end='')
        cmd = input()
finally:
    s.send("quit".encode()) # Sending quit command to keep server clean
    print("Client shutdown.")
    s.shutdown(SHUT_RDWR)
    s.close()