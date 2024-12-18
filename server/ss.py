import socket
import cv2
import pickle

# 서버 설정
HOST = '0.0.0.0'
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("서버가 시작되었습니다. 연결을 기다립니다...")
conn, addr = server_socket.accept()
print(f"{addr}에서 연결됨.")

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
