import string
import socket
import os
#import sys
#import select
#import time
#import re



# returns info from the socket
def recieve(sock):
    return sock.recv(2048).decode()

# sends info to the socket
def send(sock, data):
    return sock.send(data.encode())

def handleClientSock(cSock, addr):
    servSock.close()
    while True:
        data = recieve(cSock)
        if not data:
            break
        print("data: " + data)

        # send reply or use data
        send(cSock, 'reply: I got (' + data + ')')

    cSock.close()
    os.exit(0)      # ends the child proc

def reapChildren():
    while pidList:
        pid, stat = os.waitpid(0, os.WNOHANG)   # continue even if no child exited
        if not pid:
            break
        pidList.remove(pid)

pidList = []
servSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# servSock.bind((socket.gethostname(), 8000))
servSock.bind(('localhost', 8000))
servSock.listen(5)

while True:
    cSock, addr = servSock.accept()
    pid = os.fork()
    if pid == 0:    # child proc
        handleClientSock(cSock, addr)
    else:           # parent proc
        pidList.append(pid)
    cSock.close()

    # reap children
    reapChildren()


#s.connect(("http://www.eecs.wsu.edu/~hauser/teaching/Networks-F15/lectures/calendar.html", 80))










