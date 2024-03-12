import socket
import threading
import time
from typing import NoReturn
import os
import platform
import subprocess
import string
import requests
import ntplib
import dns.resolver
import dns.exception
from socket import gaierror

# Placeholder function for the ping oepration
def ping(host="8.8.8.8") -> NoReturn:
    """
    Simulates a ping operation. In a real application, this function would
    execute a network ping to a specified address.
    """

    # Cross-platform compatibility (different ping command arguments)
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    try:
        # Pinging
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        print(output)
    except subprocess.CalledProcessError as e:
        # If the ping command fails
        print(f'Ping request failed: {e.output}')

def check_server_http(url="http://www.google.com") -> NoReturn:
    """
    Check if an HTTP server is up by making a request to the provided URL.

    This function attempts to connect to a web server using the specified URL.
    It returns a tuple containing a boolean indicating whether the server is up,
    and the HTTP status code returned by the server.

    :param url: URL of the server (including http://)
    :return: Tuple (True/False, status code)
             True if server is up (status code < 400), False otherwise
    """
    try:
        # Making a GET request to the server
        response: requests.Response = requests.get(url)

        # The HTTP status code is a number that indicates the outcome of the request.
        # Here, we consider status codes less than 400 as successful,
        # meaning the server is up and reachable.
        # Common successful status codes are 200 (OK), 301 (Moved Permanently), etc.
        is_up: bool = response.status_code < 400

        if is_up:
            print(f"Server at {url} is up. Status Code: {response.status_code}")
        else:
            print(f"Server at {url} might be down. Status Code: {response.status_code}")

    except requests.RequestException as e:
        # This block catches any exception that might occur during the request.
        print(f"Failed to reach the server at {url}. Exception: {e}")


class PingTask(threading.Thread):
    """
    This class represents a task that performs a ping operation at regular intervals.
    It runs in a separate thread to allow concurrent execution with the server's
    command handling.
    """
    def __init__(self) -> NoReturn:
        super().__init__()
        self.paused: bool = False # Indicates if the ping task is paused
        self.stopped: bool = False # Indicates if the ping task is stopped
        self.condition: threading.Condition = threading.Condition() # Condition variable for pausing/resuming

    def run(self) -> NoReturn:
        """
        The main logic of the thread, which executes the ping operation at
        one-minute intervals, unless paused or stopped.
        """
        while not self.stopped:
            with self.condition:
                if self.paused:
                    self.condition.wait() # Wait until the task is resumed
                else:
                    ping()
            time.sleep(1) # Wait for one second

    def pause(self) -> NoReturn:
        """Pauses the ping task."""
        self.paused = True
    
    def resume(self) -> NoReturn:
        """Resumes the ping task if it was paused."""
        with self.condition:
            self.paused = False
            self.condition.notify() # Notify the thread to resume

    def stop(self) -> NoReturn:
        """Stops the ping task and the thread."""
        self.stopped = True
        if self.paused:
            self.resume() # Ensure the thread is not waiting to be resumed

class HttpTask(threading.Thread):
    """
    This class represents a task that performs a ping operation at regular intervals.
    It runs in a separate thread to allow concurrent execution with the server's
    command handling.
    """
    def __init__(self) -> NoReturn:
        super().__init__()
        self.paused: bool = False # Indicates if the ping task is paused
        self.stopped: bool = False # Indicates if the ping task is stopped
        self.condition: threading.Condition = threading.Condition() # Condition variable for pausing/resuming

    def run(self) -> NoReturn:
        """
        The main logic of the thread, which executes the ping operation at
        one-minute intervals, unless paused or stopped.
        """
        while not self.stopped:
            with self.condition:
                if self.paused:
                    self.condition.wait() # Wait until the task is resumed
                else:
                    # Call the function to print the result to the console
                    check_server_http()
            time.sleep(6) # Wait for six seconds

    def pause(self) -> NoReturn:
        """Pauses the ping task."""
        self.paused = True
    
    def resume(self) -> NoReturn:
        """Resumes the ping task if it was paused."""
        with self.condition:
            self.paused = False
            self.condition.notify() # Notify the thread to resume

    def stop(self) -> NoReturn:
        """Stops the ping task and the thread."""
        self.stopped = True
        if self.paused:
            self.resume() # Ensure the thread is not waiting to be resumed

# Class for the network server that handles client connections and commands
class Server:
    """
    This class represents a network server that listenss for incoming connections
    and handles client commands to control a ping task
    """
    def __init__(self, host: str = '127.0.0.1', port: int = 65432) -> NoReturn:
        self.host: str = host # Server host address
        self.port: int = port # Server port number
        self.ping_task: PingTask = PingTask() # The ping task managed by the server
        self.http_task: HttpTask = HttpTask()

    def start(self) -> NoReturn:
        """
        Starts the server and the ping task, then listens for incoming connections.
        Processing client commands to control the ping task
        """
        self.ping_task.start()
        self.http_task.start()


        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"Server listening on {self.host}:{self.port}")
            
            while True:
                conn, addr = s.accept()
                with conn:
                    print(f"Connected by {addr}")
                    while True:
                        data: str = conn.recv(1024).decode('ascii').upper()
                        if not data:
                            break

                        command_parts = data.split()

                        if len(command_parts) >= 2:
                            action = command_parts[0]
                            targets = command_parts[1:]

                            if action == 'PAUSE':
                                if 'HTTP' in targets:
                                    self.http_check_paused = True
                                if 'PING' in targets:
                                    self.ping_task.pause()
                                conn.sendall(b'Command executed')
                                
                            elif action == 'RESUME':
                                if 'HTTP' in targets:
                                    self.http_check_paused = False
                                if 'PING' in targets:
                                    self.ping_task.resume()
                                conn.sendall(b'Command executed')
                                
                            elif action == 'SHUTDOWN':
                                self.ping_task.stop()
                                conn.sendall(b'Server shutting down')
                                return
                        
                        else:
                            conn.sendall(b'Invalid command')

if __name__ == "__main__":
    server = Server()
    server.start()