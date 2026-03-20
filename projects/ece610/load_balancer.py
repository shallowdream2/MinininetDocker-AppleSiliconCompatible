import socket
import threading
import json


LB_IP = '10.0.0.9'
LB_PORT = 5000

# backend server (IP, Port)
BACKENDS = [
    ('20.0.0.3', 6000), # b1
    ('20.0.0.4', 6000), # b2
    ('20.0.0.5', 6000)  # b3
]


IP_TO_NAME = {
    '20.0.0.3': 'b1',
    '20.0.0.4': 'b2',
    '20.0.0.5': 'b3'
}


rr_index = 0
rr_lock = threading.Lock()

def get_next_backend():
    global rr_index
    with rr_lock:  
        backend = BACKENDS[rr_index]
        rr_index = (rr_index + 1) % len(BACKENDS)
        return backend

def handle_client(client_socket, client_address):
    try:
        client_ip = client_address[0]
        
       
        data = client_socket.recv(4096).decode('utf-8')
        if not data:
            return
            
        request_payload = json.loads(data)
        
        request_payload['client_ip'] = client_ip
        
    
        backend_ip, backend_port = get_next_backend()
        
   
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as backend_socket:
            backend_socket.connect((backend_ip, backend_port))
            backend_socket.sendall(json.dumps(request_payload).encode('utf-8'))
            
          
            backend_response = backend_socket.recv(4096).decode('utf-8')
            response_payload = json.loads(backend_response)
            
       
        returned_backend_ip = response_payload.pop('backend_ip', 'UNKNOWN')
        response_payload['backend'] = IP_TO_NAME.get(returned_backend_ip, 'UNKNOWN')
        

        client_socket.sendall(json.dumps(response_payload).encode('utf-8'))
        
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()


def start_load_balancer():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((LB_IP, LB_PORT))
    server_socket.listen(10)
    print(f"Load Balancer listening on {LB_IP}:{LB_PORT}")
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()

            client_thread = threading.Thread(
                target=handle_client, 
                args=(client_socket, client_address)
            )
            client_thread.start()
    except KeyboardInterrupt:
        print("\nShutting down Load Balancer.")
    finally:
        server_socket.close()

if __name__ == '__main__':
    start_load_balancer()