from socket import *
import threading
from Crypto.PublicKey import RSA
import json
from Crypto.Cipher import PKCS1_OAEP
import time
import os
import cv2
import pickle 
import struct
clientsAndKey = {}
clientsAndPort = {}

directory = 'Videos'
video_folder = dict()
for i in os.listdir(directory):
    video_folder[i]=[]
for i in os.listdir(directory):
    for j in os.listdir(f'{directory}/'+i):
        video_folder[i].append(directory+"/"+i+"/"+j)
print(video_folder)





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

def sendVideo(client_socket,video_name):
    print("SNDING VIDEO")
    # video_path = "Videos/BEES/1-sd_640_360_30fps.mp4"  # Replace 'your_video_file.mp4' with the path to your video file
    video_path = video_folder[video_name][0]
    video = cv2.VideoCapture(video_path)
    
    while True:
        ret, frame = video.read()
        if not ret:
            break

        # Encode frame
        _, encoded_frame = cv2.imencode('.jpg', frame)
        frame_data = pickle.dumps(encoded_frame, 0)

        # Pack frame size and frame data
        size = len(frame_data)
        packed_size = struct.pack(">L", size)

        # Send frame size and frame data
        client_socket.sendall(packed_size + frame_data)

    video.release()
    client_socket.sendall("END".encode())
    print("DONE AND ENDED")
    return 

def handleVideo(client_socket):

    # Sending the list of files to the client

    
    # Receiving the choice of video from the client
    video_requested = client_socket.recv(1024).decode()
    print("CAME",video_requested)
    print("Requested video:", video_folder[video_requested])
 
    client_socket.sendall((f"PLAYING{str(video_folder[video_requested])}").encode())


def handleClient(client_socket, address):
    print(f"Connection established from {address}")
    name = askNameAndRSA(client_socket, address)
    while True:
        try:
            message = client_socket.recv(4096)
            print(message.decode() , "RECIEVED FROM CLIENT")
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

            elif message.decode()[:4]=="PLAY":
                client_socket.send(("PLAY"+str(video_folder.keys())).encode())
                print("request for files viewing" , str(video_folder.keys()))

            elif message.decode()[:4]=="SHOW":
                client_socket.send("SHOW".encode())
                video_name = message.decode()[4:]
                sendVideo(client_socket,video_name)
                # client_socket.send(f"SHOWING{video_folder[message.decode()[4:]]}".encode())
        except Exception as e:
            print(f"Error receiving data from {address}: {str(e)}")
            break

    client_socket.close()
    print(f"Connection closed with {address}")

def start():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverPort = 5555
    serverSocket.setsockopt(SOL_SOCKET,SO_REUSEADDR, 1)
    serverSocket.bind(('localhost',serverPort))
    serverSocket.listen(10)
    print(f"Server listening on PORT: {serverPort}")
    while True:
        clientSocket, address = serverSocket.accept()
        clientThread = threading.Thread(target=handleClient, args=(clientSocket, address))
        clientThread.start()
start()