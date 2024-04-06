import socket
import json
from threading import Thread, Lock, Event
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import struct
import pickle
import warnings
import os
import sys


import cv2
import sys
sys.stderr = open('/dev/null', 'w')
lock = Lock()
name_directory = dict()
frame = None

def decrypt_message(encrypted_message, private_key):
    try:
        rsa_private_key = RSA.import_key(private_key)
        cipher = PKCS1_OAEP.new(rsa_private_key)
        decrypted_message = cipher.decrypt(encrypted_message)
        return decrypted_message.decode()
    except ValueError as e:
        print(1)
        return None

def playvideo(client_socket):
    try:
        data = b""
        payload_size = struct.calcsize(">L")
        while True:
            while len(data) < payload_size:
                data += client_socket.recv(1024)
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]

            msg_size = struct.unpack(">L", packed_msg_size)[0]

            if msg_size == 0:
                print("End of video transmission received")
                break

            while len(data) < msg_size:
                data += client_socket.recv(1024)

            frame_data = data[:msg_size]
            data = data[msg_size:]

            encoded_frame = pickle.loads(frame_data)
            frame = cv2.imdecode(encoded_frame, cv2.IMREAD_COLOR)
            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()

        print("Video streaming finished")
        return 
    except RuntimeError as e:
        print(2)
        # Suppress the error message
        
    except Exception as e:
        # # Handle other exceptions if needed
        # print("An error occurred:", str(e))
        print(3)
        cv2.destroyAllWindows()
        return



def receive_messages(client_socket, private_key,  block_event):
    global name_directory
    global lock
    while True:
        try:
            
            message = client_socket.recv(1024)
            # print(message.decode() , "RECIEVED FROM SERERER")
            if not message:
                
                break
            # print("MESSAGE FROM SERVER\n\n\n\n\n\n",message)
            if message[:4] == b'CHAT':
                encrypted_message = message[4:]
                decrypted_message = decrypt_message(encrypted_message, private_key)
                if decrypted_message:
                    print("Received message:", decrypted_message)
            elif message.decode()[:4] == "QUIT":
                print("\n" + message.decode()[4:])
                
            elif message.decode()[:4] == "NEDI":
                data = json.loads(message.decode()[4:])
                name_directory = data  # Replace the existing dictionary with the new one
                # print(name_directory.keys())
                print("Updated client directory")
                
            elif message.decode()[:4] == "PLAY":
                print("AVAILABLE FILES"  ,  message.decode()[4:])

            elif message.decode()[:4]=="SHOW":
                playvideo(client_socket)
                print("DONE WITH SHOWING")
                sys.stdout.flush()


            else:
                continue

        except ConnectionResetError:
            # print("Connection closed by server.")
            break

def get_user_input(client_socket, name, block_event):
    while True:

        user_input = input("""Type an option:\n1. Type QUIT to quit\n2. Type CHAT to chat\n3. PLAY to get list of files\n4. SHOW to play video\n""")
        if user_input.strip().upper() == "QUIT":
            client_socket.send(user_input.encode())
            break
        if user_input.strip().upper() == "CHAT":
            chat(client_socket, name)
        if user_input.strip().upper() == "PLAY":
            client_socket.sendall("PLAY".encode())
            print("Asked for PLAY")
        if user_input.strip().upper() == "SHOW":
            video_requested = input("Enter the file you want")
            client_socket.sendall(f"SHOW{video_requested}".encode())
            # playVideo(client_socket, name, lock, block_event)
        else:
            continue

def chat(client_socket, name):
    global name_directory
    for i in name_directory:
        print(i)
    whom_to_chat_with = input("Enter name of chatee\n")
    public_key = name_directory.get(whom_to_chat_with)
    if public_key is None:
        print("User not found.")
        return
    message_to_send = "MESSAGE FROM " + name + " : " + input("Enter message to send\n")
    rsa_public_key = RSA.import_key(public_key)
    cipher_rsa = PKCS1_OAEP.new(rsa_public_key)
    encrypted_message = cipher_rsa.encrypt(message_to_send.encode())
    # Combine "CHAT" and the encrypted message
    message_to_send = b"CHAT" + encrypted_message
    client_socket.send(message_to_send)
    print("Message sent successfully.")


def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 5555))
    name = input(client_socket.recv(1024).decode())
    client_socket.send(name.encode())

    key = RSA.generate(1025)
    public_key = key.publickey().export_key()
    private_key = key.export_key()
    print(client_socket.recv(1024).decode())
    c=input("Type OK to send the public key")
    if c=="OK":
            
        client_socket.send(public_key)
        print("Sent your public key")
        block_event = Event()

        # Create threads for receiving messages and getting user input
        receive_thread = Thread(target=receive_messages, args=(client_socket, private_key, block_event))
        input_thread = Thread(target=get_user_input, args=(client_socket, name, block_event))

        # Start both threads
        receive_thread.start()
        input_thread.start()

        # Wait for the input thread to finish
        input_thread.join()

        # Send QUIT message to the server before closing the socket
        client_socket.send("QUIT".encode())
        client_socket.close()
    else:
        exit()

if __name__ == "__main__":
    start_client()
