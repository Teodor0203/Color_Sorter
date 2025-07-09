import threading
import select
import bluetooth
import numpy as np

class AndroidBluetoothServer:
    def __init__(self, port=1, backlog=1, expected_mac_address=None):
        self.port = port
        self.backlog = backlog
        self.expected_mac_address = expected_mac_address.upper() if expected_mac_address else None
        self.server_sock = None
        self.client_sock = None
        self.client_info = None
        self.is_listening = False
        self.stop_event = threading.Event() # Event to signal server to stop
        print(f"BraccioBluetoothServer initialized on port: {self.port}")
        if self.expected_mac_address:
            print(f"Server configured to accept only MAC: {self.expected_mac_address}")


    def start_server(self):
        if self.server_sock:
            print("Server socket already active.")
            return True

        try:
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.server_sock.bind(("", self.port))
            self.server_sock.listen(self.backlog)
            self.is_listening = True
            print(f"Bluetooth server started and listening on port {self.port}...")
            return True
        except Exception as e:
            print(f"An unexpected error occurred during server start: {e}")
            self.server_sock = None
            self.is_listening = False
            return False

    def accept_connection(self):
        if not self.server_sock:
            print("ERROR: Server not started. Cannot accept connections.")
            return None, None

        print("Waiting for the Android App to connect...")
        try:
            while not self.stop_event.is_set():
                ready_to_read, _, _ = select.select([self.server_sock], [], [], 1) # select socket
                if ready_to_read:
                    new_client_sock, new_client_info = self.server_sock.accept()
                    connected_mac = new_client_info[0].upper() # Extract MAC address

                    if self.expected_mac_address and connected_mac != self.expected_mac_address:
                        print(f"Rejected connection from {connected_mac}. Expected: {self.expected_mac_address}")
                        new_client_sock.close() # Close unwanted connection
                        continue                # Continue waiting for the correct MAC
                    else:
                        self.client_sock = new_client_sock
                        self.client_info = new_client_info
                        print(f"Accepted connection from {self.client_info}")
                        if self.expected_mac_address:
                            print(f"Specific MAC {self.expected_mac_address} connected. Stopping server listen.")
                            self.stop_event.set()
                            if self.server_sock:
                                self.server_sock.close()
                                self.is_listening = False
                        return self.client_sock, self.client_info
            print("Server stop event received, not accepting further connections.")
            return None, None 
        except Exception as e:
            print(f"An unexpected error occurred during connection acceptance: {e}")
            self.client_sock = None
            self.client_info = None
            return None, None

    def send_data(self, client_socket, data):
        if not client_socket:
            print("ERROR: No client socket provided to send data.")
            return False
        try:
            client_socket.send(data.encode('utf-8'))
            print(f"Sent BT data to client {self.client_info}: '{data.strip()}'")
            return True
        except Exception as e:
            print(f"An unexpected error occurred during data send: {e}")
            self.close_client_connection(client_socket)
            return False

    def send_angles(self, client_socket, base_angle, shoulder_angle, elbow_angle, obj_class=0):
        if not client_socket:
            print("ERROR: No client socket provided to send angles.")
            return False

        # Clip and round angles to integers
        base_angle_int = int(np.clip(round(base_angle), 0, 180))
        shoulder_angle_int = int(np.clip(round(shoulder_angle), 0, 180))
        elbow_angle_int = int(np.clip(round(elbow_angle), 0, 180))

        # Ensure class is a single digit (0-9)
        obj_class_int = int(np.clip(round(obj_class), 0, 9))

        # Format the data string with leading zeros for fixed length
        data_string = (
            f"{base_angle_int:03d},"
            f"{shoulder_angle_int:03d},"
            f"{elbow_angle_int:03d},"
            f"{obj_class_int}\n"
        )

        try:
            client_socket.send(data_string.encode('utf-8'))
            print(f"Sent BT angles to client {self.client_info}: '{data_string.strip()}'")
            return True
        except Exception as e:
            print(f"An unexpected error occurred during angle send: {e}")
            self.close_client_connection(client_socket)
            return False

    def receive_data(self, client_socket, buffer_size=1024):
        if not client_socket:
            print("ERROR: No client socket provided to receive data.")
            return ""
        try:
            data = client_socket.recv(buffer_size).decode('utf-8').strip()
            if data:
                print(f"Received BT data from client {self.client_info}: '{data}'")
            return data
        except Exception as e:
            print(f"An unexpected error occurred during data receive: {e}")
            self.close_client_connection(client_socket)
            return ""

    def close_client_connection(self, client_socket):
        if client_socket:
            print(f"Closing client connection {self.client_info}.")
            try:
                client_socket.close()
            except Exception as e:
                print(f"Error closing client socket: {e}")
            finally:
                if client_socket == self.client_sock: # If it's the primary client
                    self.client_sock = None
                    self.client_info = None
        else:
            print("No client socket to close.")

    def stop_server(self):
        print("Signaling server to stop...")
        self.stop_event.set() # Set the event to break out of accept_connection loop
        if self.server_sock:
            print("Closing server Bluetooth socket.")
            try:
                self.server_sock.close()
            finally:
                self.server_sock = None
                self.is_listening = False
        print("Bluetooth server stopped.")

