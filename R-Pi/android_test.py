from android_bluetooth_lib import AndroidBluetoothServer
import time
import threading

PHONE_MAC = "1C:F8:D0:B6:07:BC" # REMEMBER TO REPLACE THIS WITH YOUR ANDROID PHONE'S MAC ADDRESS
PORT = 2 # Use a different port than your HC-05 connection

# Global variable to hold the client socket and a flag for connection status
connected_client_socket = None
connection_ready_event = threading.Event()

# Global variable to control the system's operational state
# 0: Stopped, 1: Running
system_start = 0 
system_start_lock = threading.Lock() # Use a lock for thread-safe access to system_start

def send_data_to_app(client_socket_param):
    """
    Function to send data to the connected Android app.
    It waits for the connection to be ready before sending.
    Sending loop is controlled by the global 'system_start' flag.
    """
    connection_ready_event.wait() # Wait until the connection is established
    if client_socket_param:
        print("\nReady to send data to the Android app. Press Ctrl+C to stop sending.")
        try:
            while True: # Continuous loop to check system_start state

                if system_start == 1:
                    for i in range(0, 4):
                        if not system_start:
                            break
                        msg = str(i) + "\n" # Added newline character
                        server.send_data(client_socket_param, msg)
                        time.sleep(2)
                else:
                    # If system_start is 0, pause briefly to avoid busy-waiting
                    time.sleep(0.5) 
        except KeyboardInterrupt:
            print("\nSender communication interrupted by user.")
        except Exception as e:
            print(f"Error during sending: {e}")
        finally:
            print("Send loop finished.")
    else:
        print("ERROR: Client socket not available for sending.")

def receive_data_from_app(client_socket_param):
    """
    Function to receive data from the connected Android app.
    It waits for the connection to be ready before receiving.
    Updates the global 'system_start' flag based on received data.
    """
    global system_start # Declare intent to modify global variable

    connection_ready_event.wait() # Wait until the connection is established
    if client_socket_param:
        print("\nReady to receive data from the Android app. Press Ctrl+C to stop receiving.")
        try:
            while True: # Continuously receive data
                received_data = server.receive_data(client_socket_param)
                if received_data:
                    try:
                        # Attempt to convert received data to integer
                        received_int_data = int(received_data)
                        with system_start_lock:
                            system_start = received_int_data # Update global flag
                        print(f"System start flag updated to: {system_start}")
                    except ValueError:
                        print(f"Warning: Received non-integer data for system_start: '{received_data}'")
                time.sleep(0.1) # Small delay to prevent busy-waiting
        except KeyboardInterrupt:
            print("\nReceiver communication interrupted by user.")
        except Exception as e:
            print(f"Error during receiving: {e}")
        finally:
            print("Receive loop finished.")
    else:
        print("ERROR: Client socket not available for receiving.")

def handle_client_connection(server_instance):
    """
    Handles accepting the client connection and setting up the global socket.
    This function blocks until a client connects.
    """
    global connected_client_socket
    
    # This call is blocking until a client connects
    client_sock, client_addr = server_instance.accept_connection()

    if client_sock:
        connected_client_socket = client_sock
        connection_ready_event.set() # Signal that the connection is established
        print(f"Connection established and ready for communication.")
    else:
        print("Failed to accept expected connection. Exiting client handler.")
        # If connection failed, ensure other threads don't wait indefinitely
        connection_ready_event.set() # Unblock other threads even on failure


if __name__ == "__main__":
    server = AndroidBluetoothServer(port=PORT, expected_mac_address=PHONE_MAC)

    if server.start_server():
        # Start a thread to handle accepting the connection
        connection_handler_thread = threading.Thread(target=handle_client_connection, args=(server,))
        connection_handler_thread.start()

        # Wait for the connection to be established by the handler thread
        print("Waiting for connection to be established by handler thread...")
        connection_ready_event.wait() # This will block until connection_ready_event.set() is called

        if connected_client_socket:
            # Once connection is ready, start send and receive threads, passing the socket
            send_thread = threading.Thread(target=send_data_to_app, args=(connected_client_socket,))
            # Receive thread is set as daemon, meaning it will terminate when the main program exits
            receive_thread = threading.Thread(target=receive_data_from_app, args=(connected_client_socket,), daemon=True)

            send_thread.start()
            receive_thread.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nMain script interrupted by user. Shutting down...")
            finally:
                pass 

        else:
            print("No client connected or connection failed. Exiting.")
    else:
        print("Failed to start Bluetooth server. Exiting.")

    print("--- Script execution finished ---")
    # Ensure server's listening socket is closed on overall script exit
    server.stop_server()
    # Close the client socket explicitly if it's still open
    if connected_client_socket:
        server.close_client_connection(connected_client_socket)
