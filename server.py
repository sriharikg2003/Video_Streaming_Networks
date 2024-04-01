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

    # Send the updated clientsAndKey dictionary to the client
    clientsAndKeyToSend = {name: key.export_key().decode() for name, key in clientsAndKey.items()}
    clientsAndKeyStr = json.dumps(clientsAndKeyToSend)
    sender_socket.send(b"NEDI"+clientsAndKeyStr.encode())

    # Update clientsAndKey and clientsAndPort dictionaries
    clientsAndKey[name] = publicKey
    clientsAndPort[name] = sender_socket

    # Broadcast the updated clientsAndKey dictionary to all clients
    broadcastClientsAndKey(clientsAndKey, clientsAndPort, sender_socket)

    return name

def create_encrypted_message(public_key, message):
    rsa_public_key = RSA.import_key(public_key)
    encrypted_message = rsa_public_key.encrypt(message.encode(), 32)
    return encrypted_message[0]

import json

def broadcastClientsAndKey(clientsAndKey, clientsAndPort, sender_socket,message=None,connect_join=None):

    if not message:
        for clientName, socket in clientsAndPort.items():
            if socket != sender_socket:
                try:
                    clientsAndKeyToSend = {}
                    for name, key in clientsAndKey.items():
                        if clientsAndPort[name] != socket:
                            # Export the RSA public key to a string representation
                            public_key_str = key.export_key().decode()
                            # Add the client name and public key to the dictionary
                            clientsAndKeyToSend[name] = public_key_str

                    # Serialize the dictionary to JSON
                    clientsAndKeyStr = json.dumps(clientsAndKeyToSend)

                    socket.send(b"NEDI"+clientsAndKeyStr.encode())
                except Exception as e:
                    print(f"Error broadcasting clientsAndKey to {clientName}: {str(e)}")

    else:
        for clientName, socket in clientsAndPort.items():
            if socket != sender_socket:
                try:
                    socket.send(b"CHAT"+message)
                except Exception as e:
                    print(f"Error broadcasting enc message to {clientName}: {str(e)}")



def handleClient(client_socket, address):
    print(f"Connection established from {address}")
    name = askNameAndRSA(client_socket, address)

    while True:
        try:
            message = client_socket.recv(4096)
            if not message:
                break
            if message[:4]==b"CHAT":
                print("CHAT")
                encrypted_message = message[4:]
                # print(encrypted_message)
                broadcastClientsAndKey(clientsAndKey, clientsAndPort, client_socket, message=encrypted_message)

            elif message.decode() == "QUIT":
                print(name, "QUITED")
                del clientsAndPort[name] 
                del clientsAndKey[name]
                for clientName, socket in clientsAndPort.items():
                    socket.send(f'QUIT{name} Left the connection'.encode())
                broadcastClientsAndKey(clientsAndKey, clientsAndPort, client_socket)
                client_socket.close()
                return 


            # print("RECV MESS", message.decode())
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