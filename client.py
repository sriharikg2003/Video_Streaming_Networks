import socket
import json
from threading import Thread
from Crypto.PublicKey import RSA
import ast
from Crypto.Cipher import PKCS1_OAEP

name_directory = dict()



def decrypt_message(encrypted_message, private_key):
    try:
        rsa_private_key = RSA.import_key(private_key)
        cipher = PKCS1_OAEP.new(rsa_private_key)
        decrypted_message = cipher.decrypt(encrypted_message)
        return decrypted_message.decode()
    except ValueError as e:
        # print("Sorry, unable to decrypt the message. This is not for you.")
        return None




def receive_messages(client_socket,private_key):
    global name_directory  # Ensure you're accessing the global variable

    while True:
        try:
            message = client_socket.recv(4096)
            # print(message)
            if not message:
                break

            if message[:4] == b'CHAT':
                encrypted_message = message[4:]
                decrypted_message = decrypt_message(encrypted_message, private_key)
                if decrypted_message:
                    print("Received decrypted message:", decrypted_message)

            elif message.decode()[:4]=="QUIT":
                print("\n"+message.decode()[4:])
                # data = json.loads(message.decode()[4:])
                # name_directory.update(data)
                # print("Updated name_directory:", name_directory)
            elif message.decode()[:4]=="NEDI":
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

    
def get_user_input(client_socket,name):
    while True:
        user_input = input("Enter your message (type 'QUIT' to quit)  (type CHAT to chat): ")
        if user_input.strip().upper() == "QUIT":
            client_socket.send(user_input.encode())
            exit()
        if user_input.strip().upper() == "CHAT":
            chat(client_socket,name)
        

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
    receive_thread = Thread(target=receive_messages, args=(client_socket,private_key))
    input_thread = Thread(target=get_user_input, args=(client_socket,name))

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
