import cv2
import cv2.aruco as aruco
from aruco_detector_lib import ObjectDetector
from braccio_robot_lib import BraccioKinematicsSolver 
from braccio_bluetooth_lib import BraccioBluetoothSender 
import numpy as np
import time

# --- Configuration for ObjectDetector ---
CALIBRATION_FILE = 'camera_calibration.npz' 
ARUCO_DICT_TYPE = aruco.DICT_6X6_250     
MARKER_LENGTH_MM = 50.0                 
MIN_OBJECT_AREA_PIXELS = 1000         

COLOR_RANGES = {
    "Red Block": {
        "lower": np.array([79, 128, 73]), 
        "upper": np.array([179, 255, 255]) 
    },
    "Green Block": {
        "lower": np.array([79, 128, 73]),  
        "upper": np.array([179, 255, 255]) 
    },
    "Blue Block": {
        "lower": np.array([79, 128, 73]), 
        "upper": np.array([179, 255, 255]) 
    }
}

# --- ArUco Marker Position in Robot's Base Frame ---
MARKER_X_IN_ROBOT_FRAME_MM = 50.0   # marker is 50mm forward of robot base
MARKER_Y_IN_ROBOT_FRAME_MM = -50.0  # marker is 50mm to the robot's right of robot base
MARKER_Z_IN_ROBOT_FRAME_MM = 0.0    # marker is on the same plane as robot's Z=0 (table)

print(f"\n--- Robot to ArUco Alignment ---")
print(f"Assuming ArUco marker center is at (X={MARKER_X_IN_ROBOT_FRAME_MM:.1f}, Y={MARKER_Y_IN_ROBOT_FRAME_MM:.1f}, Z={MARKER_Z_IN_ROBOT_FRAME_MM:.1f}) mm in the robot's base frame.")
print("!!! IMPORTANT: You MUST accurately measure and set these values. !!!")
print("-------------------------------------------\n")

# --- Bluetooth Configuration ---
HC05_MAC_ADDRESS = "98:DA:50:03:A4:B5"
BLUETOOTH_PORT = 1

detected_class = 0

# --- Initialize ObjectDetector ---
try:
    detector = ObjectDetector(
        calibration_file=CALIBRATION_FILE,
        aruco_dict_type=ARUCO_DICT_TYPE,
        marker_length_mm=MARKER_LENGTH_MM,
        color_ranges=COLOR_RANGES,
        min_object_area_pixels=MIN_OBJECT_AREA_PIXELS
    )
except FileNotFoundError:
    print("Application could not start. Please ensure calibration file exists.")
    exit()
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

# --- Braccio Robot Control Function ---
def move_braccio_to_coordinates(x_mm, y_mm, z_mm):
    print(f"\n--- BRACCIO ROBOT CONTROL ---")
    print(f"Attempting to reach target: X={x_mm:.0f}mm, Y={y_mm:.0f}mm, Z={z_mm:.0f}mm")

    # Use the Kinematics Solver to get joint angles
    joint_angles = braccio_solver.calculate_joint_angles(x_mm, y_mm, z_mm)

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
                wrist_v_angle=joint_angles['wrist_v'],
                wrist_r_angle=joint_angles['wrist_r'],
                gripper_angle=joint_angles['gripper'],
                obj_class=detected_class
            )
        else:
            print("Bluetooth not connected. Angles not sent.")

    else:
        print("Target is unreachable or angles could not be calculated.")
    print("--- END BRACCIO ROBOT CONTROL ---")

# --- Main Program Loop ---
def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        print("Please ensure your webcam is connected and not in use by another application.")
        return

    print("\n--- Starting Main Application Loop ---")
    print("Press 'q' to quit. Press 'm' to attempt a robot move to the first detected Red Block.")
    print("-------------------------------------------\n")

    while True:
        bt_connected = bt_sender.connect()
        if not bt_connected:
            print("WARNING: Bluetooth connection failed. Robot control commands will not be sent.")
            exit() 

        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame. Exiting...")
            break

        # Process the frame using the ObjectDetector library
        display_frame, aruco_data, detected_objects = detector.process_frame(frame)

        # --- Display the processed frame ---
        cv2.imshow("Real-Time Object Detection for Braccio Control", display_frame)

        # --- Braccio Robot Control Logic (Example: Move to a Red Block) ---
        first_red_block_coords = None
        for obj in detected_objects:
            if obj['color_name'] == "Red Block" and obj['rel_3d_from_aruco_mm'] is not None:
                first_red_block_coords = obj['rel_3d_from_aruco_mm']
                break

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            if first_red_block_coords:
                move_braccio_to_coordinates(
                    x_mm=first_red_block_coords[0],
                    y_mm=first_red_block_coords[1],
                    z_mm=first_red_block_coords[2]
                )
            else:
                print("\nNo Red Block detected with valid 3D coordinates to move to.")

    cap.release()
    cv2.destroyAllWindows()
    print("Main application loop finished.")

if __name__ == "__main__":
    main()