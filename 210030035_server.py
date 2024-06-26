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
# print(video_folder)





def askNameAndRSA(sender_socket, address):

    sender_socket.send("Enter your name:\n".encode())
    name = sender_socket.recv(1024).decode()
    sender_socket.send("Enter your public key \n".encode())
    publicKeyData = sender_socket.recv(1024)
    print("Recieved ",name , "Public key")
    publicKey = RSA.import_key(publicKeyData)
    # Send the updated clientsAndKey dictionary to the client
    clientsAndKeyToSend = {name: key.export_key().decode() for name, key in clientsAndKey.items()}
    clientsAndKeyStr = json.dumps(clientsAndKeyToSend)
    sender_socket.send(b"NEDI"+clientsAndKeyStr.encode())
    # Update clientsAndKey and clientsAndPort dictionaries
    clientsAndKey[name] = publicKey
    clientsAndPort[name] = sender_socket
    print(name," joined")
    # print(clientsAndKey.keys())
    # Broadcast the updated clientsAndKey dictionary to all clients
    broadcastClientsAndKey(sender_socket)
    return name

def create_encrypted_message(public_key, message):
    rsa_public_key = RSA.import_key(public_key)
    encrypted_message = rsa_public_key.encrypt(message.encode(), 32)
    return encrypted_message[0]

import json

def broadcastClientsAndKey( sender_socket,message=None,connect_join=None):
    global clientsAndKey
    global clientsAndPort
    if not message:
        print("BROADCASTING ...")
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
                    # socket.send(b"NEUS"+name.encode()+b" joined")
                    socket.send(b"NEDI"+clientsAndKeyStr.encode())
                except Exception as e:
                    pass
                    # print(f"Error broadcasting clientsAndKey to {clientName}: {str(e)}")

    else:
        for clientName, socket in clientsAndPort.items():
            if socket != sender_socket:
                try:
                    socket.send(b"CHAT"+message)
                except Exception as e:
                    pass
                    # print(f"Error broadcasting enc message to {clientName}: {str(e)}")


def sendVideo(client_socket, video_name):
    print("Sending video:", video_name)
    try:
        video_paths = video_folder.get(video_name)
        # if video_paths is None or len(video_paths) != 3:
        #     print("Invalid video files for:", video_name)
        #     return

        # Get the duration of each video (assuming all videos have the same duration)
        video = cv2.VideoCapture(video_paths[0])
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / fps
        video.release()

        # Calculate frame ranges for each portion of the video
        frame_ranges = []
        portion_duration = video_duration / 3
        for i in range(3):
            start_frame = int(i * portion_duration * fps)
            end_frame = int((i + 1) * portion_duration * fps)
            frame_ranges.append((start_frame, end_frame))

        # Iterate through each video file and send the corresponding portion
        for i, (video_path, (start_frame, end_frame)) in enumerate(zip(video_paths, frame_ranges)):
            print(f"Sending portion {i+1}/3 from video {i+1}/3")

            # Open the video file
            video = cv2.VideoCapture(video_path)

            # Set the frame position to the start of the portion
            video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            # Read and send frames until reaching the end of the portion
            while video.get(cv2.CAP_PROP_POS_FRAMES) < end_frame:
                ret, frame = video.read()
                if ret:
                    # Resize frame to fixed size
                    frame = cv2.resize(frame, (1080, 720))  # Change the size as needed

                    # Encode frame
                    _, encoded_frame = cv2.imencode('.jpg', frame)
                    frame_data = pickle.dumps(encoded_frame, 0)

                    # Pack frame size and frame data
                    size = len(frame_data)
                    packed_size = struct.pack(">L", size)
                    # Send frame size and frame data
                    client_socket.sendall(packed_size + frame_data)
                else:
                    print("Failed to read frame from video", i+1)

            video.release()

        # Send end-of-transmission marker
        client_socket.sendall(struct.pack(">L", 0))  # Zero-size packed frame indicates end of transmission

        print("Video transmission completed.")
        return 
    except Exception as e:
        # print("Error sending video:", str(e))
        return 


def handleClient(client_socket, address):
    print(f"Connection established from {address}")
    name = askNameAndRSA(client_socket, address)
    while True:
        try:
            message = client_socket.recv(1024)
            # print(message.decode() , "RECIEVED FROM CLIENT")
            if not message:
                break
            if message[:4]==b"CHAT":
                print("CHAT")
                encrypted_message = message[4:]
                # print(encrypted_message)
                broadcastClientsAndKey(client_socket, message=encrypted_message)

            elif message.decode() == "QUIT":
                print(name, "QUITED")
                del clientsAndPort[name] 
                del clientsAndKey[name]
                print("Updated client directory")
                # print(clientsAndKey.keys())
                # print(clientsAndPort.keys())
                for clientName, socket in clientsAndPort.items():
                    socket.send(f'QUIT{name} Left the connection'.encode())
                broadcastClientsAndKey( client_socket)
                client_socket.close()
                return 

            elif message.decode()[:4]=="PLAY":
                client_socket.send(("PLAY"+str(video_folder.keys())).encode())
                print("request for files viewing" , str(video_folder.keys()))

            elif message.decode()[:4]=="SHOW":
                client_socket.send("SHOW".encode())
                video_name = message.decode()[4:]
                sendVideo(client_socket,video_name)
                client_socket.send("END".encode())
                print("SENT END")
        except Exception as e:
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