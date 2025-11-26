import socket
import urllib.parse
import json
import threading
from datetime import datetime, timezone

class Request:
    def __init__(self):
        self.method = None
        self.path = None
        self.version = None
        self.headers={}
        self.query_params={}
        self.body=None
        self.id=None
DATA_STORE = {}
NEXT_ID = 1
LOCK = threading.Lock()


def generate_response(status_code, body_content, content_type="text/plain"):
    status_text={
        200:"OK",
        201:"Created",
        400:"Bad Request",
        404:"Not Found",
        500:"Internal Server Error"
    }.get(status_code, "Internal Server Error")

    status_line = f"HTTP/1.1 {status_code} {status_text}"
    body_bytes = body_content.encode('utf-8')

    headers=[
        status_line,
        f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}",
        f"Server: PythonSocket/1.0",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body_bytes)}",
        f"Connection: close"
    ]

    response = "\r\n".join(headers) + "\r\n\r\n"
    response_bytes=response.encode('utf-8')
    return response_bytes + body_bytes


def handle_root(request):
    message = "Welcome to the HTTP Server from Scratch! Routing Test Successful."
    return generate_response(200, message)
def handle_echo(request):
    message_list = request.query_params.get('message')
    if message_list and message_list[0]:
        message = message_list[0]
        body = f"Echoing: {message}"
        
        return generate_response(200, body, "text/plain")
        
    else:
        body = "400 Bad Request: Missing 'message' query parameter in the URL."
        return generate_response(400, body, "text/plain")

def handle_get_all_data(request):
    global DATA_STORE, LOCK
    LOCK.acquire()
    try:
        body = json.dumps(list(DATA_STORE.values()))
        return generate_response(200, body, "application/json")
    finally:
        LOCK.release()

def handle_get_single_data(request):
    global DATA_STORE, LOCK
    item_id = request.id
    
    LOCK.acquire()
    try:
        if item_id in DATA_STORE:
            body = json.dumps(DATA_STORE[item_id])
            return generate_response(200, body, "application/json")
        else:
            body = f"404 Not Found: Item with ID {item_id} not found."
            return generate_response(404, body, "text/plain")
    finally:
        LOCK.release()
def handle_post_data(request):
    global NEXT_ID, DATA_STORE, LOCK
    if not hasattr(request, 'body_json'):
        body = "400 Bad Request: Missing or invalid JSON body."
        return generate_response(400, body, "text/plain")
    
    LOCK.acquire()
    try:
        item_id = str(NEXT_ID)
        new_item = request.body_json
        
        new_item['id'] = item_id 
        
        DATA_STORE[item_id] = new_item
        NEXT_ID += 1
        
        body = json.dumps(new_item)
        return generate_response(201, body, "application/json")
        
    except Exception as e:
        return generate_response(500, f"500 Internal Error during POST: {e}", "text/plain")
        
    finally:
        LOCK.release()
def handle_put_data(request):
    global DATA_STORE, LOCK
    item_id = request.id

    if item_id not in DATA_STORE:
        body = f"404 Not Found: Item with ID {item_id} cannot be updated."
        return generate_response(404, body, "text/plain")

    if not hasattr(request, 'body_json'):
        body = "400 Bad Request: Missing or invalid JSON body for update."
        return generate_response(400, body, "text/plain")
        
    LOCK.acquire()
    try:
        updated_item = request.body_json
        updated_item['id'] = item_id 
        
        DATA_STORE[item_id] = updated_item
        
        body = json.dumps(updated_item)
        return generate_response(200, body, "application/json")
        
    except Exception as e:
        return generate_response(500, f"500 Internal Error during PUT: {e}", "text/plain")

    finally:
        LOCK.release()

ROUTES = {
    "GET": {
        "/": handle_root,
        "/echo": handle_echo,
        "/data": handle_get_all_data,
        "/data/id": handle_get_single_data
    },
    "POST": {
        "/data": handle_post_data
    },
    "PUT": {
        "/data/id": handle_put_data
    }
}
def find_handler(method, path):
    if method in ROUTES:
        method_routes = ROUTES[method]
        
        if path in method_routes:
            return method_routes[path], None

        path_parts = path.strip('/').split('/')
        if len(path_parts) == 2 and path_parts[0] == 'data':
            resource_id = path_parts[1]
            if '/data/id' in method_routes:
                return method_routes['/data/id'], resource_id
                
    return None, None

def read_full_request(client_socket):
    request_data=b""
    header_end=b"\r\n\r\n"

    while header_end not in request_data:
        chunk = client_socket.recv(1024)
        if not chunk:
            return b""
        request_data+=chunk

    header_end_index = request_data.find(header_end)

    header_bytes = request_data[:header_end_index]
    initial_body_bytes = request_data[header_end_index + 4:]
    headers_str = header_bytes.decode("utf-8", errors="ignore").lower()

    content_length=0
    search_key="content-length:"

    if search_key in headers_str:
        try:
            start_index = headers_str.find(search_key) + len(search_key)
            end_index = headers_str.find('\r\n', start_index)
            if end_index == -1:
                end_index = len(headers_str)
                
            length_str = headers_str[start_index:end_index].strip()
            content_length = int(length_str)
            
        except ValueError:
            content_length = 0
    
    body_length_read = len(initial_body_bytes)
    missing_bytes = content_length - body_length_read

    if missing_bytes>0:
        remaining_body = b''
        while len(remaining_body) < missing_bytes:
            chunk = client_socket.recv(missing_bytes - len(remaining_body))
            if not chunk:
                break
            remaining_body += chunk
        
        request_data += remaining_body
        
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

        header_break = data.find(b'\r\n\r\n')
        if header_break != -1:
            body_bytes = data[header_break + 4:]
            
            if request.method in ["POST", "PUT"]:
                request.body = body_bytes
                
                content_type = request.headers.get('content-type', '').lower()
                if 'application/json' in content_type:
                    try:
                        decoded_body = request.body.decode('utf-8')
                        cleaned_body_str = decoded_body.strip().replace('\x00', '')
                        print(f"\n[DEBUG] Cleaned Body (Length {len(cleaned_body_str)}): '{cleaned_body_str}'")
                        request.body_json = json.loads(cleaned_body_str) 
                        
                    except json.JSONDecodeError as json_e:
                        print(f"DEBUG: JSONDecodeError details: {json_e}")
                        raise ValueError("Invalid JSON body payload.")

        return request


    except Exception as e:
        print("error occured: ",e)
        return None

    finally:
        print("Parsing completed")

def handle_client_connection(client_socket, client_address):
    print(f"Accepted connection from {client_address}")

    try:
        request_data = read_full_request(client_socket)
        if not request_data:
            return
            
        request = parse_request(request_data)
        response_bytes = None
        
        if request is None:
            response_bytes = generate_response(400, "400: Malformed Request", "text/plain")
        
        else:
            handler, resource_id = find_handler(request.method, request.path)
            
            if handler:
                request.id = resource_id 
                response_bytes = handler(request)
            else:
                response_bytes = generate_response(404, "<h1>404 Not Found</h1>", "text/html")
                
            print(f"Method: {request.method}")
            print(f"Path: {request.path}")
            print(f"Headers (Host): {request.headers.get('host', 'N/A')}")
            print(f"Query Params: {request.query_params}")

        client_socket.sendall(response_bytes)

    except Exception as e:
        # Final catch for any unexpected runtime errors
        print(f"Error handling client {client_address}: {e}")
        response_bytes = generate_response(500, "<h1>500 Internal Server Error</h1>", "text/html")
        client_socket.sendall(response_bytes) 
    
    finally:
        try:
            client_socket.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        client_socket.close()
        print(f"Connection with {client_address} closed.")

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