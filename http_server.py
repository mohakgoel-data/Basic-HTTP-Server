import socket

def handle_client_connection(client_socket,client_address):
    print(f"Accepted connection from {client_address}")

    try:
        request_data=client_socket.recv(4096)
        if not request_data:
            return
        print("\n--- Raw Request Data ---")
        print(request_data.decode('utf-8', errors='ignore'))
        print("------------------------\n")

        dummy_response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 20\r\nConnection: close\r\n\r\nServer is responding."
        client_socket.sendall(dummy_response.encode('utf-8'))

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")

    finally:
        client_socket.close()
        print("Client connection closed")

def run_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"server running on {host}, {port}")
        while True:
            client_socket, client_address = server_socket.accept()
            handle_client_connection(client_socket, client_address)
    except KeyboardInterrupt:
        print("server shutting down")
    finally:
        server_socket.close()


HOST = '127.0.0.1'
PORT = 8080

if __name__ == '__main__':
    run_server(HOST, PORT)