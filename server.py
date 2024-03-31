from socket import *
import threading
from Crypto.PublicKey import RSA
import json
from Crypto.Cipher import PKCS1_OAEP

clientsAndKey = {}
clientsAndPort = {}


def askNameAndRSA(sender_socket, address):
    sender_socket.send("Enter your name:\n".encode())
    name = sender_socket.recv(1024).decode()
    publicKeyData = sender_socket.recv(4096)
    publicKey = RSA.import_key(publicKeyData)
    clientsAndKeyStr = str(clientsAndKey)
    sender_socket.send(clientsAndKeyStr.encode())
    clientsAndKey[name] = publicKey
    clientsAndPort[name] = sender_socket

    broadcastClientsAndKey(clientsAndKey, clientsAndPort ,sender_socket)
    return name


def broadcastClientsAndKey(clientsAndKey, clientsAndPort, sender_socket):

    for clientName, socket in clientsAndPort.items():
        if socket != sender_socket:
            try:
                clientsAndKeyToSend = {name: key for name, key in clientsAndKey.items() if clientsAndPort[name] != socket}
                
                clientsAndKeyStr = str(clientsAndKeyToSend)
                socket.send(clientsAndKeyStr.encode())
            except Exception as e:
                print(f"Error broadcasting clientsAndKey to {clientName}: {str(e)}")





def handleClient(client_socket, address):
    print(f"Connection established from {address}")
    name = askNameAndRSA(client_socket, address)

    while True:
        try:
            message = client_socket.recv(4096)
            if not message:
                break

            if message.decode()=="QUIT":
                print(name ,"QUITED")
                del clientsAndPort[name] 
                del clientsAndKey[name]
                for clientName, socket in clientsAndPort.items():
                    socket.send(f'{name} Left the connection'.encode())
                broadcastClientsAndKey(clientsAndKey, clientsAndPort, client_socket)
                client_socket.close()
                return 
            print("RECV MESS" ,message.decode())
        except Exception as e:
            print(f"Error receiving data from {address}: {str(e)}")
            break

    client_socket.close()
    print(f"Connection closed with {address}")


def start():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverPort = 5555
    serverSocket.setsockopt(SOL_SOCKET,SO_REUSEADDR, 1)
    serverSocket.bind(('',serverPort))
    serverSocket.listen(10)
    print(f"Server listening on PORT: {serverPort}")

    while True:
        clientSocket, address = serverSocket.accept()
        clientThread = threading.Thread(target=handleClient, args=(clientSocket, address))
        clientThread.start()

start()