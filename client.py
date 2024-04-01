import socket
import json
from threading import Thread
from Crypto.PublicKey import RSA
import ast

name_directory = dict()
def receive_messages(client_socket):
    global name_directory  # Ensure you're accessing the global variable

    while True:
        try:
            message = client_socket.recv(4096)
            print(message.decode())
            if not message:
                break
            
            # Decode the received message as JSON and update name_directory
            data = json.loads(message.decode())
            name_directory.update(data)

            print("Updated name_directory:", name_directory)

        except ConnectionResetError:
            print("Connection closed by server.")
            break
def get_user_input(client_socket):
    while True:
        user_input = input("Enter your message (type 'QUIT' to quit)  (type CHAT to chat): ")
        client_socket.send(user_input.encode())
        if user_input.strip().upper() == "QUIT":
            exit()
        

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('', 5555))
    name = input(client_socket.recv(1024).decode())
    client_socket.send(name.encode())

    key = RSA.generate(1025)
    public_key = key.publickey().export_key()
    private_key = key.export_key()

    client_socket.send(public_key)
    print("Sent your public key")

    # Create threads for receiving messages and getting user input
    receive_thread = Thread(target=receive_messages, args=(client_socket,))
    input_thread = Thread(target=get_user_input, args=(client_socket,))

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
