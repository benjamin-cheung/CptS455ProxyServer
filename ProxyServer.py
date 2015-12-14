import string
import socket
import os
import sys
import signal
import re

# returns info from the socket
def recieve(sock, numBytes = None):
    data = ''
    if numBytes is None:    # recieve until socket is empty
        while True:
            byte = sock.recv(1)
            if not byte:
                break
            data += byte
            if '\r\n\r\n' in data:
                break
    else:
        while numBytes > 0: # recieve a specific number of bytes
            byte = sock.recv(1)
            if not byte:
                break
            data += byte
            numBytes -= 1
    return data

# recieves all chunks from the webserver and returns as one string
def recieveChunks(sock):
    data = ''
    while True:
        chunk = ''
        # read in chunk length
        while '\r\n' not in chunk:
            byte = sock.recv(1)
            if not byte:
                break
            chunk += byte
        # check if chunk was empty
        if len(chunk.strip()) == 0:
            break
        
        length = int(str(chunk.strip()), 16)
        chunk = recieve(sock, length)
        data += chunk
    return data

# sends info to the socket
def send(sock, data):
    return sock.send(data)

# takes the data string and parses it into a dictionary
def parseHeader(data):
    return dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", data))

# checks if the data to be recieved is chunked
def checkChunked(hdr):
    isChunked = False
    if 'Transfer-Encoding' in hdr.keys():
        if 'chunked' == hdr['Transfer-Encoding']:
            isChunked = True
#    if 'Content-Length' not in hdr.keys():
#        isChunked = True
    return isChunked

# determines how to handle content to be recieved from server
def handleServerResponse(servSock, clientSock, hdr, data):
    isChunked = checkChunked(hdr)
    contLength = 0
    # recieve chunked content
    if isChunked:
        data += recieveChunks(servSock)
        send(clientSock, data)
    # recieve content all at once
    elif 'Content-Length' in hdr.keys():
        contLength = int(hdr['Content-Length'])
        if contLength > 0:
            data += recieve(servSock, contLength)
        else:
            data += recieve(servSock)
        send(clientSock, data)
    # no content to recieve
    else:
        send(clientSock, data)

# determines how to handle client requests
def handleClientSock(clientSock, addr):
    while True:
        data = recieve(clientSock)
        # end loop when client has no requests or responses
        if not data:
            break
        
        hdrClient = parseHeader(data)
        # allows requests to successfully go through the WSU firewall
        data.replace('GET http://' + hdrClient['Host'], 'GET ')
        data.replace('GET ' + hdrClient['Host'], 'GET ')
        # create socket and connect to host
        connInfo = str(hdrClient['Host']).split(':')
        servSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if len(connInfo) > 1:
            servSock.connect((str(connInfo[0]), int(connInfo[1]) ))
        else:
            servSock.connect((str(connInfo[0]), 80))
        
        # Adds POST content to data for POST requests
        if 'POST' in data:
            print('CLIENT POST REQUEST HEADER ONLY:\n' + data)
            data += recieve(clientSock, int(hdrClient['Content-Length']))
        else:
            print('CLIENT HTTP REQUEST\n' + data)
        
        send(servSock, data)
        data = recieve(servSock)
        # handles server responses
        if data:
            hdrServer = parseHeader(data)
            print('SERVER HTTP RESPONSE:\n' + data)
            handleServerResponse(servSock, clientSock, hdrServer, data)

        # closes server socket
        if 'Connection' in hdrServer.keys() and hdrServer['Connection'] == 'close':
            servSock.close()
    
    # clean up and end proc
    clientSock.close()
    os._exit(0)


proxySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxySock.bind(('localhost', 65535))
proxySock.listen(5)

signal.signal(signal.SIGCHLD, signal.SIG_IGN)   # avoids child zombie procs

while True:
    clientSock, addr = proxySock.accept()
    pid = os.fork()
    if pid == 0:    # child proc
        handleClientSock(clientSock, addr)

# http://www.eecs.wsu.edu/~hauser/teaching/Networks-F15/lectures/calendar.html





