import string
import socket
import os
import sys
import signal
import re


# returns info from the socket

def recieve(sock, numBytes = None):
    data = ''
    if numBytes is None:
        while True:
            byte = sock.recv(1).decode()
            if not byte:
                break
            data += byte        
            if data[-4:] == '\r\n\r\n':
                break;
    else:
        data += sock.recv(numBytes).decode()
    return data

def recieveChunkSize(sock):
    length = ''
    while True:
        byte = sock.recv(1).decode()
        if not byte:
            break;
        length += byte
        if data[-2:] == '\r\n':
            break
    return int(length.strip(), 16)

# sends info to the socket
def send(sock, data):
    return sock.send(data.encode())

def parseHeader(data):
    return dict(re.findall(r"[?<=\n]([a-zA-Z0-9\-]*): (.*)\r\n?", data))

def handleClientSock(clientSock, addr):
    isChunked = False
    while True:
        data = recieve(clientSock)
        if not data:
            break
        print('\nFROM CLIENT BROWSER\n' + data)
        
        hdrClient = parseHeader(data)
        # hdrClient.update(dict(re.findall(r"^(GET) (.*) ", data)))
        
        webInfo = str(hdrClient['Host']).split(':')
        servSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if len(webInfo) > 1:
            servSock.connect((str(webInfo[0]), int(webInfo[1]) ))
        else:
            servSock.connect((str(webInfo[0]), 80))

        # send data to web server
        send(servSock, data)
        # recieve header from web server
        data = recieve(servSock)

        hdrServer = parseHeader(data)
        
        if 'Transfer-Encoding' in hdrServer.keys():
            if 'chunked' == hdrServer['Transfer-Encoding']:
                isChunked = True
        
        contLength = 0
        if 'Content-Length' in hdrServer.keys():
            contLength = int(hdrServer['Content-Length'])

        if isChunked:
            size = recieveChunkSize(serveSock)
            
            
            
        else:
            if contLength > 0:
                data += recieve(servSock, int(hdrServer['Content-Length']))
            else:        
                data += recieve(servSock)
        print('\nFROM WEBSERVER\n' + data)
        servSock.close()
        send(clientSock, data)
    
    clientSock.close()
    os.exit(0)      # ends the child proc


proxySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxySock.bind(('localhost', 8000))
proxySock.listen(5)

signal.signal(signal.SIGCHLD, signal.SIG_IGN)   # avoids child zombie procs

while True:
    clientSock, addr = proxySock.accept()
    pid = os.fork()
    if pid == 0:    # child proc
        handleClientSock(clientSock, addr)
    clientSock.close()

# http://www.eecs.wsu.edu/~hauser/teaching/Networks-F15/lectures/calendar.html













