import socket
import sys
import json
import hashlib
import uuid
def read_graph_file(filepath):
    edges = []
    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                edges.append(parts)
    return edges

def build_graph_dict(edges):
    graph = {}
    for a, b in edges:
        if a not in graph:
            graph[a] = []
        graph[a].append(b)
        if b not in graph:
            graph[b] = []
    return graph

def send_graph_to_lb(graph, lb_ip, lb_port):
    
    req_id = str(uuid.uuid4())
    payload = json.dumps({"graph": graph, "req_id": req_id})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((lb_ip, lb_port))
        s.sendall(payload.encode())
        response = s.recv(1024).decode()
        print(f"[Client] Received response from LB: {response}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 client.py input_file.txt lb_ip_address lb_port")
        sys.exit(1)

    filepath = sys.argv[1]
    lb_ip = sys.argv[2]
    lb_port = int(sys.argv[3])
    edges = read_graph_file(filepath)
    graph = build_graph_dict(edges)
    send_graph_to_lb(graph, lb_ip=lb_ip, lb_port=lb_port)
