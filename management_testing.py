import socket
import time
import threading
from typing import Dict, NoReturn

# Hardcoded configuration for the monitoring services
MONITORING_SERVICES = {
    'service1': {'ip': '192.168.1.10', 'port': 65432},
    'service2': {'ip': '192.168.1.11', 'port': 65433},
    # Add more monitoring services as needed
}

# Class for the management client that connects to multiple monitoring services
class ManagementClient:
    def __init__(self) -> NoReturn:
        self.connections: Dict[str, socket.socket] = {}
        self.connect_to_services()

    def connect_to_services(self) -> NoReturn:
        for service_id, service_info in MONITORING_SERVICES.items():
            try:
                conn = socket.create_connection((service_info['ip'], service_info['port']))
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Enable TCP Keepalive
                self.connections[service_id] = conn
                print(f"Connected to {service_id} at {service_info['ip']}:{service_info['port']}")
            except socket.error as e:
                print(f"Could not connect to {service_id}: {e}")

    def reconnect_service(self, service_id: str) -> NoReturn:
        service_info = MONITORING_SERVICES.get(service_id)
        if service_info:
            try:
                self.connections[service_id].close()
                conn = socket.create_connection((service_info['ip'], service_info['port']))
                conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                self.connections[service_id] = conn
                print(f"Reconnected to {service_id} at {service_info['ip']}:{service_info['port']}")
            except socket.error as e:
                print(f"Could not reconnect to {service_id}: {e}")

    def send_command(self, service_id: str, command: str) -> NoReturn:
        if service_id in self.connections:
            try:
                self.connections[service_id].sendall(command.encode('ascii'))
                response = self.connections[service_id].recv(1024)
                print(f"{service_id} response: {response.decode('ascii')}")
            except socket.error:
                print(f"Connection lost with {service_id}. Attempting to reconnect.")
                self.reconnect_service(service_id)

    def start(self) -> NoReturn:
        while True:
            service_id = input("Enter service ID (or 'EXIT' to quit): ")
            if service_id.upper() == 'EXIT':
                print("Exiting client.")
                break
            command = input("Enter command (PAUSE, RESUME, SHUTDOWN): ").upper()
            self.send_command(service_id, command)

if __name__ == "__main__":
    client = ManagementClient()
    client.start()