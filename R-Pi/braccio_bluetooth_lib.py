import bluetooth
import numpy as np
import sys 

class BraccioBluetoothSender:
    def __init__(self, mac_address, port=1):
        self.mac_address = mac_address
        self.port = port
        self.sock = None
        print(f"BraccioBluetoothSender initialized for MAC: {self.mac_address}, Port: {self.port}")

    def connect(self):
        if self.sock:
            print("Already connected to Bluetooth.")
            return True

        try:
            print(f"Attempting to connect to HC-05 at {self.mac_address} on port {self.port}...")
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.sock.connect((self.mac_address, self.port))
            print("Successfully connected to HC-05!")
            return True
        except bluetooth.btcommon.BluetoothError as e:
            if "Connection refused" in str(e):
                print(f"Bluetooth connection error: Connection refused. Is the HC-05 paired and powered on?")
            elif "Host is down" in str(e) or "No route to host" in str(e):
                print(f"Bluetooth connection error: HC-05 not found or out of range. Check power and proximity.")
            elif sys.platform.startswith('linux') and "[Errno 112]" in str(e):
                 print(f"Bluetooth connection error (Linux): Device not ready or already in use. Try `sudo rfcomm release hci0` or `sudo systemctl restart bluetooth`")
            else:
                print(f"Bluetooth connection error: {e}")
            self.sock = None
            return False
        except Exception as e:
            print(f"An unexpected error occurred during Bluetooth connection: {e}")
            self.sock = None
            return False

    def send_angles(self, base_angle, shoulder_angle, elbow_angle, wrist_v_angle, wrist_r_angle, gripper_angle, obj_class=0):
        if not self.sock:
            print("ERROR: Not connected to Bluetooth. Cannot send data.")
            return False

        base_angle_int = int(np.clip(round(base_angle), 0, 180))
        shoulder_angle_int = int(np.clip(round(shoulder_angle), 0, 180))
        elbow_angle_int = int(np.clip(round(elbow_angle), 0, 180))
        wrist_v_angle_int = int(np.clip(round(wrist_v_angle), 0, 180))
        wrist_r_angle_int = int(np.clip(round(wrist_r_angle), 0, 180))
        gripper_angle_int = int(np.clip(round(gripper_angle), 0, 180))
        
        # Ensure class is a single digit
        obj_class_int = int(np.clip(round(obj_class), 0, 9))

        # Format the data string with leading zeros for fixed length
        data_string = (
            f"{base_angle_int:03d},"
            f"{shoulder_angle_int:03d},"
            f"{elbow_angle_int:03d},"
            f"{wrist_v_angle_int:03d},"
            f"{wrist_r_angle_int:03d},"
            f"{gripper_angle_int:03d},"
            f"{obj_class_int}\n" 
        )

        try:
            self.sock.send(data_string.encode('utf-8'))
            print(f"Sent BT data: '{data_string.strip()}'")
            return True
        except bluetooth.btcommon.BluetoothError as e:
            print(f"Bluetooth send error: {e}. Connection lost?")
            self.disconnect()
            return False
        except Exception as e:
            print(f"An unexpected error occurred during Bluetooth send: {e}")
            self.disconnect()
            return False

    def disconnect(self):
        """Closes the Bluetooth connection if it's open."""
        if self.sock:
            print("Closing Bluetooth socket.")
            try:
                self.sock.close()
            except Exception as e:
                print(f"Error closing Bluetooth socket: {e}")
            finally:
                self.sock = None
        else:
            print("Bluetooth socket is already closed or not connected.")