import socket
import urllib.parse

class Request:
    def __init__(self):
        self.method = None
        self.path = None
        self.version = None
        self.headers={}
        self.query_params={}
        self.body=None
        self.id=None

def read_full_request(client_socket):
    request_data=b""
    header_end=b"\r\n\r\n"

    while header_end not in request_data:
        chunk = client_socket.recv(1024)
        if not chunk:
            return b""
        request_data+=chunk
    
    return request_data

def parse_request(data):
    request=Request()

    try:
        request_str=data.decode("utf-8")
        lines = request_str.split('\r\n')

        request_line = lines[0]
        parts = request_line.split(' ')
        if len(parts) != 3:
            raise ValueError("Malformed request line")
        request.method, full_path, request.version = parts
        url_parts = urllib.parse.urlparse(full_path)
        request.path = url_parts.path
        request.query_params=urllib.parse.parse_qs(url_parts.query)

        for line in lines[1:]:
            if not line:
                break

            key, value=line.split(":",1)
            request.headers[key.strip().lower()]=value.strip()

        return request


    except Exception as e:
        print("error occured: ",e)
        return None

    finally:
        print("Parsing completed")

def handle_client_connection(client_socket,client_address):
    print(f"Accepted connection from {client_address}")

    try:
        request_data=read_full_request(client_socket)
        if not request_data:
            return
        request=parse_request(request_data)

        print(f"Method: {request.method}")
        print(f"Path: {request.path}")
        print(f"Headers (Host): {request.headers.get('host', 'N/A')}")
        print(f"Query Params: {request.query_params}")

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