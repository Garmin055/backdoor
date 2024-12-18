# server.py
import socket

def start_server():
    host = '0.0.0.0'  # 서버가 수신할 모든 인터페이스
    port = 9999       # 서버 포트

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"서버가 {port} 포트에서 실행 중입니다.")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"클라이언트 연결됨: {client_address}")

        try:
            while True:
                command = input("명령어 입력 ('fetch' 또는 'exit'): ").strip()
                client_socket.send(command.encode())

                if command == 'fetch':
                    log_data = client_socket.recv(4096).decode()
                    print(f"클라이언트 로그:\n{log_data}")
                elif command == 'exit':
                    print("클라이언트와의 연결 종료.")
                    client_socket.close()
                    break
        except Exception as e:
            print(f"에러 발생: {e}")
            client_socket.close()
            break

if __name__ == "__main__":
    start_server()
