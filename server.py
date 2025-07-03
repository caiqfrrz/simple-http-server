import socket
import os
import threading
import json

class HttpServer:
    def __init__(self, config_file='config.json', host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.server_name = config.get("server_name", "My HTTP server")
        self.blacklist_dirs = config.get("blacklist_dir", [])
        self.blacklist_files = config.get("blacklist_files", [])

    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        print(f"Listening on {self.host}:{self.port}")

        while True:
            client_sock, addr = self.sock.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=self.handle_client, args=(client_sock,)).start()

    def handle_client(self, client_sock):
        request = client_sock.recv(1024).decode()
        print("REQUEST:")
        print(request)

        self.handle_response(client_sock, request)
        client_sock.close()
    
    def handle_response(self, client_sock, request):
        first = str.split(request.partition('\n')[0])
        method = first[0]
        location = first[1]
        protocol_version = first[2]
        response = ""

        if location == '/':
            location += 'index.html'

        filepath = location.lstrip('/')

        if self.is_blacklisted(filepath):
            response = self.build_response_header("403", protocol_version)
            client_sock.sendall(response.encode())
            return

        if method == "GET":
            if not os.path.isfile(filepath):
                response = self.build_response_header("404", protocol_version)
                client_sock.sendall(response.encode())
            else:
                filetype = self.get_content_type(filepath)
                with open(filepath, 'rb') as f:
                    content = f.read()

                response = self.build_response_header("200", protocol_version, filetype, len(content))
                client_sock.sendall(response.encode() + content)

    def build_response_header(self, code, protocol_version, content_type='text/html', content_length=0):
        response = f"{protocol_version} {code}"
        
        if code == "404":
            response = response + " Not found\r\n"
        elif code == "403":
            response = response + " Forbidden\r\n"
        elif code == "200":
            response = response + " OK\r\n"

        headers = (
            f"Server: {self.server_name}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: close\r\n"
            "\r\n"
        )

        return response + headers
    
    def is_blacklisted(self, filepath):
        filename = os.path.basename(filepath)
        if filename in self.blacklist_files:
            return True
        
        for d in self.blacklist_dirs:
            if os.path.abspath(filepath).startswith(os.path.abspath(d)):
                return True
        return False

    def get_content_type(self, filename):
        if filename.endswith('.html'):
            return 'text/html'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            return 'image/jpeg'
        else:
            return 'application/octet-stream' 

if __name__ == '__main__':
    http = HttpServer()
    http.start()