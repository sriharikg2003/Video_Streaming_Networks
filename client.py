import socket
import json
from threading import Thread
from Crypto.PublicKey import RSA
import ast
from threading import Thread, Event
from Crypto.Cipher import PKCS1_OAEP
import time
import cv2
import numpy as np

name_directory = dict()
frame = None

def decrypt_message(encrypted_message, private_key):
    try:
        rsa_private_key = RSA.import_key(private_key)
        cipher = PKCS1_OAEP.new(rsa_private_key)
        decrypted_message = cipher.decrypt(encrypted_message)
        return decrypted_message.decode()
    except ValueError as e:
        # print("Sorry, unable to decrypt the message. This is not for you.")
        return None

def receive_messages(client_socket, private_key, block_event):
    global name_directory

    while True:
        try:
            if block_event.is_set():
                print("Trying to access illegal thread")
                
            else:
                message = client_socket.recv(4096)
                print(message)
                if not message:
                    break
                if message[:4] == b'CHAT':
                    encrypted_message = message[4:]
                    decrypted_message = decrypt_message(encrypted_message, private_key)
                    if decrypted_message:
                        print("Received decrypted message:", decrypted_message)
                elif message.decode()[:4] == "QUIT":
                    print("\n" + message.decode()[4:])
                    # data = json.loads(message.decode()[4:])
                    # name_directory.update(data)
                    # print("Updated name_directory:", name_directory)
                elif message.decode()[:4] == "NEDI":
                    # print("NEEDID")
                    data = json.loads(message.decode()[4:])
                    name_directory.update(data)
                    print(name_directory)
        except ConnectionResetError:
            print("Connection closed by server.")
            break


def chat(client_socket,name):
    for i in name_directory:
        print(i)
    whom_to_chat_with = input("Enter name of chatee\n")
    public_key = name_directory[whom_to_chat_with]
    message_to_send = "MESSAGE FROM " +name + " : " + input("Enter message to send\n")
    rsa_public_key = RSA.import_key(public_key)
    cipher_rsa = PKCS1_OAEP.new(rsa_public_key)
    encrypted_message = cipher_rsa.encrypt(message_to_send.encode())
    # Combine "CHAT" and the encrypted message
    message_to_send = b"CHAT" + encrypted_message
    # print(message_to_send)
    client_socket.send(message_to_send)
    print("Message sent successfully.")
    return 
    
def playVideo(client_socket, name, block_event):
    block_event.set()  # Set the event to block other threads

    print("Other thread is blocked")

    # Send "PLAY" command to the server
    client_socket.sendall("PLAY".encode())

    # Receive video list from the server
    response = client_socket.recv(1024).decode()
    if not response:
        print("Server didn't respond with video list.")
        block_event.clear()
        return

    print("Obtained video list:", response)

    # Get the video file name from the user
    video_filename = input("Enter the file name you want to play: ")
    client_socket.send(video_filename.encode())
    print("Sent", video_filename, "for playback.")

    # Receive the video content from the server
    video_content = client_socket.recv(1024).decode()
    print("Received video content:", video_content)

    # Clear the block event to unblock other threads
    block_event.clear()


def get_user_input(client_socket,name,block_event):
    while True:
        user_input = input("Enter your message (type 'QUIT' to quit)  (type CHAT to chat): ")
        if user_input.strip().upper() == "QUIT":
            client_socket.send(user_input.encode())
            exit()
        if user_input.strip().upper() == "CHAT":
            chat(client_socket,name)

        if user_input.strip().upper() == "PLAY":
            print("Asked for PLAy")
            playVideo(client_socket, name, block_event)
        

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 5555))
    name = input(client_socket.recv(1024).decode())
    client_socket.send(name.encode())

    key = RSA.generate(1025)
    public_key = key.publickey().export_key()
    private_key = key.export_key()

    client_socket.send(public_key)
    print("Sent your public key")
    block_event = Event()
    # Create threads for receiving messages and getting user input
    receive_thread = Thread(target=receive_messages, args=(client_socket,private_key,block_event))
    input_thread = Thread(target=get_user_input, args=(client_socket,name,block_event))

    # Start both threads
    receive_thread.start()
    input_thread.start()

    # Wait for the input thread to finish
    input_thread.join()

    # Send QUIT message to the server before closing the socket
    client_socket.send("QUIT".encode())
    client_socket.close()

if __name__ == "__main__":
    start_client()
