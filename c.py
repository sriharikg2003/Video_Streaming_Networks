# import cv2
# import io
# import socket
# import struct
# import time
# import pickle
# import numpy as np
# import imutils


# client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# # client_socket.connect(('0.tcp.ngrok.io', 19194))
# client_socket.connect(('localhost', 5555))

# cam = cv2.VideoCapture(0)
# img_counter = 0

# #encode to jpeg format
# #encode param image quality 0 to 100. default:95
# #if you want to shrink data size, choose low image quality.
# encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]

# while True:
#     ret, frame = cam.read()
#     # 影像縮放
#     frame = imutils.resize(frame, width=320)
#     # 鏡像
#     frame = cv2.flip(frame,180)
#     result, image = cv2.imencode('.jpg', frame, encode_param)
#     data = pickle.dumps(image, 0)
#     size = len(data)

#     if img_counter%10==0:
#         client_socket.sendall(struct.pack(">L", size) + data)
#         cv2.imshow('client',frame)
        
#     img_counter += 1

#     # 若按下 q 鍵則離開迴圈
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
    

# cam.release()



import cv2
import socket
import struct
import pickle

# Socket setup
HOST = 'localhost'
PORT = 5555

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

data = b""
payload_size = struct.calcsize(">L")

while True:
    while len(data) < payload_size:
        data += client_socket.recv(4096)

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]

    msg_size = struct.unpack(">L", packed_msg_size)[0]

    while len(data) < msg_size:
        data += client_socket.recv(4096)

    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Decode frame
    encoded_frame = pickle.loads(frame_data)
    frame = cv2.imdecode(encoded_frame, cv2.IMREAD_COLOR)

    # Display frame
    cv2.imshow('Video', frame)

    # Check for 'q' key press to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
client_socket.close()
