# # Import the required modules
# from IPython.display import clear_output
# import socket
# import sys
# import cv2
# import matplotlib.pyplot as plt
# import pickle
# import numpy as np
# import struct ## new
# import zlib
# from PIL import Image, ImageOps

# HOST='localhost'
# PORT=5555

# s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# print('Socket created')

# s.bind((HOST,PORT))
# print('Socket bind complete')
# s.listen(10)
# print('Socket now listening')

# conn,addr=s.accept()

# data = b""
# payload_size = struct.calcsize(">L")
# print("payload_size: {}".format(payload_size))
# while True:
#     while len(data) < payload_size:
#         data += conn.recv(4096)
#         if not data:
#             cv2.destroyAllWindows()
#             conn,addr=s.accept()
#             continue
#     # receive image row data form client socket
#     packed_msg_size = data[:payload_size]
#     data = data[payload_size:]
#     msg_size = struct.unpack(">L", packed_msg_size)[0]
#     while len(data) < msg_size:
#         data += conn.recv(4096)
#     frame_data = data[:msg_size]
#     data = data[msg_size:]
#     # unpack image using pickle 
#     frame=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
#     frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

#     cv2.imshow('server',frame)
#     cv2.waitKey(1)

import cv2
import socket
import struct
import pickle

# Open the video file
video_path = "Videos/BEES/1-sd_640_360_30fps.mp4"  # Replace 'your_video_file.mp4' with the path to your video file
video = cv2.VideoCapture(video_path)

# Socket setup
HOST = 'localhost'
PORT = 5555

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server listening on port {PORT}")

conn, addr = server_socket.accept()

print('Client connected:', addr)

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
    conn.sendall(packed_size + frame_data)

video.release()
server_socket.close()
