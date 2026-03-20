import socket
import threading
import json

def count_vertices(graph_dict):
    return len(graph_dict)

def handle_connection(conn, addr):
    try:
        data = conn.recv(4096)
        if not data:
            return

        request = json.loads(data.decode())
        graph = request.get("graph", {})
        req_id = request.get("req_id", "unknown")
        client_ip = request.get("client_ip", "unknown")
        backend_ip = conn.getsockname()[0]    

        result = count_vertices(graph)
        response = json.dumps({"vertex_count": result, "req_id": req_id, "client_ip": client_ip, "backend_ip": backend_ip})
        conn.sendall(response.encode())

    except Exception as e:
        print(f"[Backend] Error: {e}")
        conn.sendall(b"Error processing request")
    finally:
        conn.close()

def start_backend_server(host="0.0.0.0", port=6000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[Backend] Listening on {host}:{port}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_connection, args=(conn, addr)).start()

if __name__ == "__main__":
    start_backend_server()
