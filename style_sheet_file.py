import socket
import threading

server = "127.0.0.1"
port = 4444
udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server_socket.bind((server, port))
print("server runs")

def handle_udp_message(data, address):
    print(f"UDP message from {address}: {data.decode()}")


def listen_udp():
    while True:
        try:
            # Receive the message length (4 bytes)
            len, _ = udp_server_socket.recvfrom(4)
            print(len)
            data, address = udp_server_socket.recvfrom(1024)
            threading.Thread(target=handle_udp_message, args=(data, address)).start()
        except OSError as os_err:
            print(f"OS error: {os_err}")
        except Exception as e:
            print(f"Exception: {e}")


def main():
    udp_thread = threading.Thread(target=listen_udp)
    udp_thread.start()


if __name__ == '__main__':
    main()