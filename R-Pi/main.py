import cv2
import cv2.aruco as aruco
from aruco_detector_lib import ObjectDetector
from braccio_robot_lib import BraccioKinematicsSolver
from braccio_bluetooth_lib import BraccioBluetoothSender
from android_bluetooth_lib import AndroidBluetoothServer
import numpy as np
import time
import threading

# For Pi Camera
from picamera2 import Picamera2, Preview
# --- Initialize Picamera2 ---
picam2 = Picamera2()
camera_config = picam2.create_still_configuration(main={"size": (1280, 720), "format": "BGR888"})
picam2.configure(camera_config)
picam2.start()

# --- Configuration for ObjectDetector ---
CALIBRATION_FILE = 'camera_calibration.npz'
ARUCO_DICT_TYPE = aruco.DICT_6X6_250
MARKER_LENGTH_MM = 50.0
MIN_OBJECT_AREA_PIXELS = 1000

ready_event = threading.Event()

data = 0
detected_colour = 0

COLOR_RANGES = {
    "Red Block": {
        "lower": np.array([117,130,199]),
        "upper": np.array([145, 255, 255])
    },
    "Pink Block": {
        "lower": np.array([151,48,186]),
        "upper": np.array([179,255,255])
    },
    "Yellow Block": {
        "lower": np.array([77,111,115]),
        "upper": np.array([100,255,255])
    },
    "Blue Block": {
        "lower": np.array([0,250,0]),
        "upper": np.array([179, 255, 255])
    }
}

# --- ArUco Marker Position in Robot's Base Frame ---
MARKER_X_IN_ROBOT_FRAME_MM = 120.0   # marker is 120mm forward of robot base
MARKER_Y_IN_ROBOT_FRAME_MM = -70.0   # marker is 70mm to the robot's right of robot base
MARKER_Z_IN_ROBOT_FRAME_MM = 0.0     # marker is on the same plane as robot's Z=0 (table)

print(f"\n--- Robot to ArUco Alignment ---")
print(f"Assuming ArUco marker center is at (X={MARKER_X_IN_ROBOT_FRAME_MM:.1f}, Y={MARKER_Y_IN_ROBOT_FRAME_MM:.1f}, Z={MARKER_Z_IN_ROBOT_FRAME_MM:.1f}) mm in the robot's base frame.")
print("-------------------------------------------\n")

# --- Bluetooth Configuration ---
HC05_MAC_ADDRESS = "98:DA:50:03:A4:B5"
BLUETOOTH_PORT = 1

PHONE_MAC = "1C:F8:D0:B6:07:BC"
PORT = 2 

was_data_sent = False

system_start_lock = threading.Lock()
system_start = 0 

connected_client_socket = None
connection_ready_event = threading.Event()

# --- Initialize ObjectDetector ---
try:
    detector = ObjectDetector(
        calibration_file=CALIBRATION_FILE,
        aruco_dict_type=ARUCO_DICT_TYPE,
        marker_length_mm=MARKER_LENGTH_MM,
        color_ranges=COLOR_RANGES,
        min_object_area_pixels=MIN_OBJECT_AREA_PIXELS
    )
except Exception as e:
    print(f"Application could not start due to detector initialization error: {e}")
    exit()

# --- Initialize Braccio Kinematics Solver ---
braccio_solver = BraccioKinematicsSolver()

# --- Initialize Bluetooth Sender ---
bt_sender = BraccioBluetoothSender(
    mac_address=HC05_MAC_ADDRESS,
    port=BLUETOOTH_PORT
)

# --- Initialize Android Bluetooth Server ---
server = AndroidBluetoothServer(
    port=PORT,
    expected_mac_address=PHONE_MAC
)

# --- Braccio Robot Control Function ---
def move_braccio_to_coordinates(x_target_robot_frame_mm, y_target_robot_frame_mm, z_target_robot_frame_mm, detected_class=1):
    print(f"\n--- BRACCIO ROBOT CONTROL ---")
    print(f"Attempting to reach target (Robot Frame): X={x_target_robot_frame_mm:.0f}mm, Y={y_target_robot_frame_mm:.0f}mm, Z={z_target_robot_frame_mm:.0f}mm")

    joint_angles = braccio_solver.calculate_joint_angles(x_target_robot_frame_mm, y_target_robot_frame_mm, z_target_robot_frame_mm)
    if(joint_angles == None):
        return 1, 1

    if joint_angles:
        print("Calculated Joint Angles (Degrees):")
        for joint, angle in joint_angles.items():
            print(f"  {joint.replace('_', ' ').title()}: {angle:.1f} degrees")
        
        # --- SEND ANGLES OVER BLUETOOTH ---
        if bt_sender.sock:
            bt_sender.send_angles(
                base_angle=joint_angles['base'],
                shoulder_angle=joint_angles['shoulder'],
                elbow_angle=joint_angles['elbow'],
                obj_class=detected_class
            )
            print("Data sent")
        else:
            print("Bluetooth not connected. Angles not sent.")
        
    else:
        print("Target is unreachable or angles could not be calculated. No angles sent via Bluetooth.")
    print("-------------------------------------------\n")
    return 0, 0

def get_coords(obj):
    obj_y_from_marker = obj['rel_3d_from_aruco_mm'][1]
    obj_x_from_marker = obj['rel_3d_from_aruco_mm'][0]
    obj_z_from_marker = obj['rel_3d_from_aruco_mm'][2]
                    
    # Convert object coordinates relative to marker to robot base frame
    target_x_robot = MARKER_X_IN_ROBOT_FRAME_MM + obj_x_from_marker
    target_y_robot = MARKER_Y_IN_ROBOT_FRAME_MM + obj_y_from_marker
    target_z_robot = MARKER_Z_IN_ROBOT_FRAME_MM + obj_z_from_marker
                    
    return (target_x_robot, target_y_robot, target_z_robot)

def camera():
    global data
    global was_data_sent
    global detected_colour

    try:
        while True:
            # Capture frame 
            frame = picam2.capture_array("main")
            
            if frame is None:
                print("Failed to grab frame. Exiting...")
                break

            # Process the frame using the ObjectDetector
            display_frame, aruco_data, detected_objects = detector.process_frame(frame)

            # --- Display the processed frame ---
            cv2.imshow("Real-Time Object Detection for Braccio Control", display_frame)

            detected_block = [0,0,0]
            detected_colour = 0                                                           
            if(len(detected_objects) != 0):
                if detected_objects[0]['color_name'] == "Red Block" and detected_objects[0]['rel_3d_from_aruco_mm'] is not None:
                    detected_block = get_coords(detected_objects[0])
                    detected_colour = 0
                elif detected_objects[0]['color_name'] == "Pink Block" and detected_objects[0]['rel_3d_from_aruco_mm'] is not None:
                    detected_block = get_coords(detected_objects[0])
                    detected_colour = 1
                elif detected_objects[0]['color_name'] == "Blue Block" and detected_objects[0]['rel_3d_from_aruco_mm'] is not None:
                    detected_block = get_coords(detected_objects[0])
                    detected_colour = 2
                elif detected_objects[0]['color_name'] == "Yellow Block" and detected_objects[0]['rel_3d_from_aruco_mm'] is not None:
                    detected_block = get_coords(detected_objects[0])
                    detected_colour = 3

            if(system_start):    
                if(data):
                    was_data_sent, data = move_braccio_to_coordinates(
                        x_target_robot_frame_mm=detected_block[0],
                        y_target_robot_frame_mm=detected_block[1],
                        z_target_robot_frame_mm=detected_block[2],
                        detected_class = detected_colour
                    )
                
                if not was_data_sent:
                    if client_sock:
                        msg = str(detected_colour) + "\n"
                        server.send_data(client_sock, msg)
                        print(f"Sent {msg} to android app!")
                        was_data_sent = True

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break   

        

    except Exception as e:
        print(f"An error occurred during script execution: {e}")
    finally:
        # --- Cleanup ---
        picam2.stop()
        cv2.destroyAllWindows()
        if bt_connected:
            bt_sender.disconnect()
        print("Main application loop finished.")

def ready():
    global data
    while True:
        data = bt_sender.receive_ready()
        if(data):
            print("Received ready!")

def android_receive():
    global system_start
    global client_sock
    if client_sock:
        print("\nReady to receive data from the Android app. Press Ctrl+C to stop receiving.")
        try:
            while True:
                received_data = server.receive_data(client_sock)
                if received_data:
                    try:
                        received_int_data = int(received_data)
                        with system_start_lock:
                            system_start = received_int_data
                        print(f"System start flag updated to: {system_start}")
                    except ValueError:
                        print(f"Warning: Received non-integer data for system_start: '{received_data}'")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nReceiver communication interrupted by user.")
        except Exception as e:
            print(f"Error during receiving: {e}")
        finally:
            print("Receive loop finished.")
    else:
        print("ERROR: Client socket not available for receiving.")

if __name__ == "__main__":    
    time.sleep(2) # Delay for picam

    print("\n--- Starting Main Application Loop ---")
    
    bt_connected = bt_sender.connect()
    if not bt_connected:
        print("WARNING: Bluetooth connection failed. Robot control commands will not be sent.")

    if server.start_server():
        client_sock, client_addr = server.accept_connection()
        if not client_sock:
            print("WARNING: Bluetooth connection to android app failed. Colour data will not be sent.")
        else:
            print(f"Connection established and ready for communication.")


    t1 = threading.Thread(target=camera)
    t2 = threading.Thread(target=ready, daemon=True) 
    t3 = threading.Thread(target=android_receive, daemon=True)

    t1.start()
    t2.start()
    t3.start()

    t1.join()