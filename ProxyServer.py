# Benjamin Cheung
# CptS 455 Computer Networking
# Project 3 - Proxy Server
# December 13, 2015

import string
import socket
import os
import sys
import signal
import re

# returns info from the socket
def receive(sock, numBytes = None):
    data = ''
    if numBytes is None:    # receive until socket is empty
        while True:
            byte = sock.recv(1)
            if not byte:
                break
            data += byte
            if '\r\n\r\n' in data:
                break
    else:
        while numBytes > 0: # receive a specific number of bytes
            byte = sock.recv(1)
            if not byte:
                break
            data += byte
            numBytes -= 1
    return data

# receives all chunks from the webserver and returns as one string
def receiveChunks(sock):
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
        chunk = receive(sock, length)
        data += chunk
    return data

# sends info to the socket
def send(sock, data):
    return sock.send(data)

# takes the data string and parses it into a dictionary
def parseHeader(data):
    return dict(re.findall(r"(?P<name>.*?): (?P<value>.*?)\r\n", data))

# checks if the data to be received is chunked
def checkChunked(hdr):
    isChunked = False
    if 'Transfer-Encoding' in hdr.keys():
        if 'chunked' == hdr['Transfer-Encoding']:
            isChunked = True
#    if 'Content-Length' not in hdr.keys():
#        isChunked = True
    return isChunked

# determines how to handle content to be received from server
def handleServerResponse(servSock, clientSock, hdr, data):
    isChunked = checkChunked(hdr)
    contLength = 0
    # receive chunked content
    if isChunked:
        data += receiveChunks(servSock)
        send(clientSock, data)
    # receive content all at once
    elif 'Content-Length' in hdr.keys():
        contLength = int(hdr['Content-Length'])
        if contLength > 0:
            data += receive(servSock, contLength)
        else:
            data += receive(servSock)
        send(clientSock, data)
    # no content to receive
    else:
        send(clientSock, data)

# determines how to handle client requests
def handleClientSock(clientSock, addr):
    while True:
        data = receive(clientSock)
        # end loop when client has no requests or responses
        if not data:
            break
        
        hdrClient = parseHeader(data)
        # allows requests to successfully go through the WSU firewall
        data = data.replace('GET http://' + hdrClient['Host'], 'GET ')
        data = data.replace('GET ' + hdrClient['Host'], 'GET ')
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
            data += receive(clientSock, int(hdrClient['Content-Length']))
        else:
            print('CLIENT HTTP REQUEST\n' + data)
        
        send(servSock, data)
        data = receive(servSock)
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

# Testing Websites
# http://www.eecs.wsu.edu/~hauser/teaching/Networks-F15/lectures/calendar.html
# www.cnn.com
