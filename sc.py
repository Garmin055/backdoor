import socket
import cv2
import pyautogui
import pickle
import numpy as np

# 클라이언트 설정
SERVER_IP = '192.168.0.3'
PORT = 9999

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

try:
    while True:
        # 화면 캡처
        screenshot = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # 데이터 직렬화 및 전송
        data = pickle.dumps(frame)
        client_socket.sendall(len(data).to_bytes(4, 'big') + data)
except Exception as e:
    print(f"오류 발생: {e}")
finally:
    client_socket.close()
