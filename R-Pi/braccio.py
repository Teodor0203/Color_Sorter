from ultralytics import YOLO
import cv2
import math
import numpy as np 
import bluetooth

HC05_MAC_ADDRESS = "98:DA:50:03:A4:B5" 
PORT = 1  # Standard Bluetooth Serial Port Profile (SPP) port

# Initialize Bluetooth socket
bt_sock = None

try:
    print(f"Attempting to connect to HC-05 at {HC05_MAC_ADDRESS} on port {PORT}...")
    # Create a Bluetooth socket using RFCOMM protocol (for serial communication)
    bt_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    # Connect to the specified MAC address and port
    bt_sock.connect((HC05_MAC_ADDRESS, PORT))
    print("Successfully connected to HC-05!")
except bluetooth.btcommon.BluetoothError as e:
    print(f"Bluetooth connection error: {e}")
    print("Please ensure:")
    print("1. The HC-05 is powered on and in pairing/discoverable mode.")
    print("2. The HC-05 is paired with your Raspberry Pi.")
    print("3. The HC05_MAC_ADDRESS in the script is correct.")
    print("4. The Bluetooth service is running on your Pi (`sudo systemctl status bluetooth`).")
except Exception as e:
    print(f"An unexpected error occurred: {e}")


# 1. Braccio Arm Dimensions (in millimeters)
# DE MODIFICAT!!!!
BRACCIO_BASE_HEIGHT = 70.0        # Height from the robot's base plate to the shoulder joint pivot
BRACCIO_UPPER_ARM_LENGTH = 125.0  # Shoulder to Elbow pivot
BRACCIO_FOREARM_LENGTH = 125.0    # Elbow to Wrist pivot
BRACCIO_HAND_LENGTH = 120.0       # Wrist pivot to the point you want to grasp (e.g., gripper tips)

# 2. Braccio Joint Limits (in degrees) DE MODIFICAT!!!
THETA0_MIN, THETA0_MAX = 0, 180  # Base
THETA1_MIN, THETA1_MAX = 0, 180  # Shoulder 
THETA2_MIN, THETA2_MAX = 0, 180  # Elbow
THETA3_MIN, THETA3_MAX = 0, 180  # Wrist Pitch 
THETA4_MIN, THETA4_MAX = 0, 180  # Wrist Roll 

# 3. Camera Parameters and Camera-to-Robot Alignment
CAM_WIDTH_PIXELS = 640
CAM_HEIGHT_PIXELS = 480

# 4. Camera Position relative to Robot Base    DE MODIFICAT!!!!!
CAMERA_HEIGHT_FROM_ROBOT_BASE = 500.0 # mm

# Define the real-world coordinates of a known reference point in your camera's view.
# Let's assume the center of the camera's view (CAM_WIDTH_PIXELS/2, CAM_HEIGHT_PIXELS/2)
# corresponds to (ROBOT_BASE_CENTER_X_MM, ROBOT_BASE_CENTER_Y_MM) in the robot's X-Y plane.
# Adjust these values based on your actual setup.
ROBOT_BASE_CENTER_X_MM = 0.0 # Example: Robot base origin is at (0,0) in its own frame
ROBOT_BASE_CENTER_Y_MM = 0.0 # Example

# Estimate pixel-to-mm scaling factor. DE MODIFICAT!!!!
# use object of known size to measure size in pixel ??
REAL_WORLD_VIEW_WIDTH_MM = 350.0  # Random value
REAL_WORLD_VIEW_HEIGHT_MM = (CAM_HEIGHT_PIXELS / CAM_WIDTH_PIXELS) * REAL_WORLD_VIEW_WIDTH_MM

MM_PER_PIXEL_X = REAL_WORLD_VIEW_WIDTH_MM / CAM_WIDTH_PIXELS
MM_PER_PIXEL_Y = REAL_WORLD_VIEW_HEIGHT_MM / CAM_HEIGHT_PIXELS

# Z Coodrinate, set to something small
TARGET_OBJECT_Z_ROBOT_FRAME = 50.0 # mm (50 mm above base plate)


# Inverse Kinematics Function
def solve_braccio_ik(target_x, target_y, target_z):
    """
    Solves inverse kinematics for a simplified Braccio arm model.
    Assumes a 3-DOF planar arm for shoulder/elbow/wrist_pitch, plus base rotation.

    Args:
        target_x (float): Target X coordinate in robot base frame (mm).
        target_y (float): Target Y coordinate in robot base frame (mm).
        target_z (float): Target Z coordinate in robot base frame (mm).

    Returns:
        tuple: (theta0, theta1, theta2, theta3, theta4) in degrees, or None if unreachable.
               theta0: Base rotation
               theta1: Shoulder angle
               theta2: Elbow angle
               theta3: Wrist pitch (up/down)
               theta4: Gripper rotation (fixed here for simplicity, or could be passed)
    """

    # --- 1. Calculate Base Angle (theta0) ---
    theta0 = math.degrees(math.atan2(target_y, target_x))
    if not (THETA0_MIN <= theta0 <= THETA0_MAX):
        print(f"IK Error: Base angle ({theta0:.2f} deg) out of limits! ({THETA0_MIN}-{THETA0_MAX})")
        return None

    # --- 2. Project 3D point to 2D for 3-link planar arm (Shoulder, Elbow, Wrist Pitch) ---
    # Convert to a 2D problem in the arm's plane
    # The X coordinate in the arm's plane is the distance from the base pivot (projected_x)
    projected_x = math.sqrt(target_x**2 + target_y**2)

    # The Z coordinate for the planar arm needs to account for the robot's base height
    # This is the height of the target relative to the shoulder joint's pivot
    planar_z = target_z - BRACCIO_BASE_HEIGHT

    # We need to consider the third link (hand) when calculating the target for the elbow.
    # If the end-effector (gripper tip) is at (x, z), and we want the gripper to be vertical (pointing down),
    # then the wrist joint (end of forearm) needs to be at (x, z + BRACCIO_HAND_LENGTH).
    # This is a common simplification for pick and place.
    target_wrist_x = projected_x
    target_wrist_z = planar_z + BRACCIO_HAND_LENGTH # Adjust for wrist height if gripper points downwards

    # Calculate distance from shoulder to target wrist point
    D = math.sqrt(target_wrist_x**2 + target_wrist_z**2)

    # Check if the target wrist point is reachable by the upper arm and forearm
    if D > (BRACCIO_UPPER_ARM_LENGTH + BRACCIO_FOREARM_LENGTH):
        print(f"IK Error: Target ({D:.2f} mm) too far (upper arm + forearm = {BRACCIO_UPPER_ARM_LENGTH + BRACCIO_FOREARM_LENGTH:.2f} mm)!")
        return None
    if D < abs(BRACCIO_UPPER_ARM_LENGTH - BRACCIO_FOREARM_LENGTH):
        print(f"IK Error: Target ({D:.2f} mm) too close (min reach = {abs(BRACCIO_UPPER_ARM_LENGTH - BRACCIO_FOREARM_LENGTH):.2f} mm)!")
        return None

    # --- 3. Solve for Shoulder (theta1) and Elbow (theta2) ---
    # Using the Law of Cosines for the triangle formed by (Shoulder, Elbow, Target_Wrist)

    # Elbow angle (theta2, in radians)
    # The cosine of the angle at the elbow (inside the triangle)
    cos_theta2_internal = (BRACCIO_UPPER_ARM_LENGTH**2 + BRACCIO_FOREARM_LENGTH**2 - D**2) / (2 * BRACCIO_UPPER_ARM_LENGTH * BRACCIO_FOREARM_LENGTH)
    # Due to floating point inaccuracies, clip to valid range [-1, 1]
    cos_theta2_internal = np.clip(cos_theta2_internal, -1.0, 1.0)
    
    # Braccio convention: Elbow angle (J2) typically defined such that 90 deg is straight.
    # The actual angle of the elbow servo should be 180 - internal_angle for a standard setup where 0 is fully bent inwards.
    # Or, if 90 is straight, then 90 - (internal_angle / 2) is needed.
    # Let's use the internal angle and map to Braccio's 0-180 range.
    # A common Braccio IK maps the angle of the elbow relative to the shoulder.
    # If the angle we just calculated is the internal angle of the elbow joint, we need to convert it.
    # Many Braccio IK solutions use:
    # theta2_rad = math.acos((D**2 - BRACCIO_UPPER_ARM_LENGTH**2 - BRACCIO_FOREARM_LENGTH**2) / (2 * BRACCIO_UPPER_ARM_LENGTH * BRACCIO_FOREARM_LENGTH))
    theta2_rad = math.acos(cos_theta2_internal) # This is the internal angle of the triangle at the elbow

    # Shoulder angle (theta1, in radians)
    alpha = math.atan2(target_wrist_z, target_wrist_x) # Angle of vector from shoulder to wrist target
    beta = math.acos((BRACCIO_UPPER_ARM_LENGTH**2 + D**2 - BRACCIO_FOREARM_LENGTH**2) / (2 * BRACCIO_UPPER_ARM_LENGTH * D))
    beta = np.clip(beta, 0.0, math.pi) # Ensure beta is in [0, pi]

    theta1_rad = alpha - beta # Standard solution for 'elbow down' configuration

    # --- 4. Calculate Wrist Pitch Angle (theta3) ---
    # This angle aims to orient the gripper. If we want the gripper to be vertical (pointing down),
    # the sum of the angles (shoulder + elbow + wrist pitch) should result in a vertical orientation.
    # Assuming:
    #   theta1 is absolute angle from base X-axis
    #   theta2 is relative to the previous link (upper arm)
    #   theta3 is relative to the previous link (forearm)
    # Total angle of the hand from the base X-axis = theta1_rad + theta2_rad + theta3_rad
    # For gripper pointing vertically down, this total angle should be -90 degrees (-pi/2 radians).
    # So, theta3_rad = -math.pi/2 - theta1_rad - theta2_rad

    # However, Braccio's convention for J3 (wrist) is often 0-180 where 90 is straight.
    # If the goal is for the hand to be vertical (relative to ground),
    # the angle of the forearm relative to horizontal is (theta1_rad + theta2_rad).
    # Then theta3 needs to bring it to -90 degrees.
    # theta3_rad = (-math.pi / 2) - (theta1_rad + theta2_rad) # If J3 is absolute angle from horizontal
    # More commonly, theta3 is relative to the forearm.
    # If theta1 is shoulder angle from horizontal, theta2 is elbow angle from upper arm.
    # Then the forearm angle from horizontal is (theta1_rad + theta2_rad)
    # To point straight down: The angle of the hand from the forearm must be such that (forearm_angle + hand_angle) = -PI/2
    # So, theta3_rad = (-math.pi / 2) - (theta1_rad + theta2_rad)
    # Let's use the convention: if 0 is straight, then 90 is usually vertical down.
    # So, the desired angle for the gripper relative to its own base (the wrist joint)
    # is 90 degrees if it's pointing straight down.
    # The actual angle of the forearm relative to the ground is theta1_rad + theta2_rad.
    # If J3 (wrist) is measured from the forearm, then for vertical:
    theta3_rad = (math.pi / 2) - (theta1_rad + theta2_rad) # Assuming positive angles are CCW from horizontal for IK
                                                         # And Braccio's J3 servo 90deg is vertical down

    # --- Convert to Degrees and Apply Offsets/Mapping to Servo Ranges ---
    theta1_deg = math.degrees(theta1_rad)
    theta2_deg = math.degrees(theta2_rad)
    theta3_deg = math.degrees(theta3_rad)

    # Apply offsets/mapping to Braccio's specific servo conventions (0-180 degrees)
    # These offsets are CRITICAL and depend on your Braccio's assembly and what 0/90/180 means for its servos.
    # The typical Braccio starts with J1 around 15-20, J2 around 160.
    # If your IK gives angles where 0 is "straight" and 90 is "up/down" for shoulder/elbow,
    # you might need to adjust them to the Braccio's range.
    # For example, if J1 (shoulder) 0 is fully down and 180 is fully up:
    # A standard setup maps IK output to 0-180 directly, but the interpretation of '0' for each joint varies.

    # Common Braccio servo mapping examples (adjust based on your Braccio's default positions):
    # J0 (Base): theta0_deg (usually 0-180 direct map)
    # J1 (Shoulder): 180 - theta1_deg (if IK gives 0=straight, 180=vertical up, and servo is 0=up, 180=down)
    # J2 (Elbow): 180 - theta2_deg (if IK gives 0=straight, 180=vertical up, and servo is 0=bent, 180=straight)
    # J3 (Wrist Pitch): 90 - theta3_deg (if IK gives 0=horizontal, 90=vertical, and servo is 0=up, 180=down)

    # For now, let's assume the IK gives angles that can be directly mapped to the servos (0-180 range).
    # You will likely need to tweak these conversions heavily with your physical robot.

    # Validate against joint limits
    if not (THETA1_MIN <= theta1_deg <= THETA1_MAX):
        print(f"IK Error: Shoulder angle ({theta1_deg:.2f} deg) out of limits! ({THETA1_MIN}-{THETA1_MAX})")
        return None
    if not (THETA2_MIN <= theta2_deg <= THETA2_MAX):
        print(f"IK Error: Elbow angle ({theta2_deg:.2f} deg) out of limits! ({THETA2_MIN}-{THETA2_MAX})")
        return None
    if not (THETA3_MIN <= theta3_deg <= THETA3_MAX):
        print(f"IK Error: Wrist Pitch angle ({theta3_deg:.2f} deg) out of limits! ({THETA3_MIN}-{THETA3_MAX})")
        return None

    # theta4 is for wrist roll (J4), not usually involved in XYZ position, more for orientation
    # We'll fix it to a neutral position for now (e.g., 90 degrees)
    theta4_deg = 90.0 # Wrist Roll (Gripper rotation) - fixed for simple pick/place
    if not (THETA4_MIN <= theta4_deg <= THETA4_MAX):
        print(f"IK Error: Wrist Roll angle ({theta4_deg:.2f} deg) out of limits! ({THETA4_MIN}-{THETA4_MAX})")
        return None


    # Return angles in degrees (converted to int for easier Arduino parsing)
    # You might want to keep them float for more precision and convert to int just before sending.
    return (int(theta0), int(theta1_deg), int(theta2_deg), int(theta3_deg), int(theta4_deg))

# Build the message with the coords and detected class and send it over bluetooth
def send_data(theta0, theta1, theta2, theta3, theta4, cls):
    data = ""
    
    if(theta0 < 10):
        data += (f"00{theta0}")
    else:
        if(theta0 < 100):
            data +=(f"0{theta0}")
        else:
            data += (f"{theta0}")
    
    data += ","

    if(theta1 < 10):
        data += (f"00{theta1}")
    else:
        if(theta1 < 100):
            data +=(f"0{theta1}")
        else:
            data += (f"{theta1}")
    
    data += ","

    if(theta2 < 10):
        data += (f"00{theta2}")
    else:
        if(theta2 < 100):
            data +=(f"0{theta2}")
        else:
            data += (f"{theta2}")
    
    data += ","

    if(theta3 < 10):
        data += (f"00{theta3}")
    else:
        if(theta3 < 100):
            data +=(f"0{theta3}")
        else:
            data += (f"{theta3}")
    
    data += ","

    if(theta4 < 10):
        data += (f"00{theta4}")
    else:
        if(theta4 < 100):
            data +=(f"0{theta4}")
        else:
            data += (f"{theta4}")
    
    data += (f",{cls}")

    print(data) # DEBUG!!
    bt_sock.send(data.encode('utf-8'))


# load model
model = YOLO("model.pt")

# List of images to process
image_paths = [
    # "test_images/test1.jpg",
    # "test_images/test2.jpg",
    "test_images/test3.jpg",
    # "test_images/test4.jpg",
    # "test_images/test5.jpg",
    # "test_images/test6.jpg",
    # "test_images/test7.jpg",
]

# Process each image
for image_path in image_paths:
    results = model(image_path)

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image {image_path}")
        continue
    img_height, img_width, _ = img.shape

    print(f"\nProcessing image: {image_path}")

    # Extract detections
    for result in results:
        for box in result.boxes:
            x1_pixel, y1_pixel, x2_pixel, y2_pixel = box.xyxy[0].cpu().numpy().astype(int) # Ensure integer and on CPU
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            # Calculate centroid of the bounding box in pixel coordinates
            center_x_pixel = (x1_pixel + x2_pixel) / 2
            center_y_pixel = (y1_pixel + y2_pixel) / 2

            print(f"Detected: {model.names[cls]} at pixel center ({center_x_pixel:.0f}, {center_y_pixel:.0f}) with {conf:.2f} confidence.")

            # Calculate pixel offset from the camera's center
            offset_x_pixels = center_x_pixel - (CAM_WIDTH_PIXELS / 2)
            offset_y_pixels = center_y_pixel - (CAM_HEIGHT_PIXELS / 2)

            robot_x = offset_x_pixels * MM_PER_PIXEL_X + ROBOT_BASE_CENTER_X_MM
            robot_y = offset_y_pixels * MM_PER_PIXEL_Y + ROBOT_BASE_CENTER_Y_MM

            robot_z = TARGET_OBJECT_Z_ROBOT_FRAME # Fixed Z for objects on table

            print(f"Estimated Robot Coordinates (mm): X={robot_x:.2f}, Y={robot_y:.2f}, Z={robot_z:.2f}")

            # IK
            joint_angles = solve_braccio_ik(robot_x, robot_y, robot_z)

            # Print in terminal - DEBUG
            if joint_angles:
                theta0, theta1, theta2, theta3, theta4 = joint_angles
                print(f"Calculated Braccio Angles (degrees):")
                if(theta0 < 10):
                    print(f"  Base (J0): 0{theta0}")
                else:
                    if(theta0 < 100):
                        print(f"  Base (J0): 0{theta0}")
                    else:
                        print(f"  Base (J0): {theta0}")
                
                if(theta1 < 10):
                    print(f"  Shoulder (J1): 00{theta1}")
                else:
                    if(theta1 < 100):
                        print(f"  Shoulder (J1): 0{theta1}")
                    else:
                        print(f"  Shoulder (J1): {theta1}")
                
                if(theta2 < 10):
                    print(f"  Elbow (J2): 00{theta2}")
                else:
                    if(theta2 < 100):
                        print(f"  Elbow (J2): 0{theta2}")
                    else:
                        print(f"  Elbow (J2): {theta2}")
                
                if(theta3 < 10):
                    print(f"  Wrist Pitch (J3): 00{theta3}")
                else:
                    if(theta3 < 100):
                        print(f"  Wrist Pitch (J3): 0{theta3}")
                    else:
                        print(f"  Wrist Pitch (J3): {theta3}")
                
                if(theta4 < 10):
                    print(f"  Wrist Roll (J4 - fixed): 00{theta4}")
                else:
                    if(theta4 < 100):
                        print(f"  Wrist Roll (J4 - fixed): 0{theta4}")
                    else:
                        print(f"  Wrist Roll (J4 - fixed): {theta4}")
            else:
                print("Could not find a valid IK solution for this target.")

            # Send to STM32
            send_data(theta0, theta1, theta2, theta3, theta4, cls)

            # Draw bounding box and object center  - DEBUG!!
            cv2.rectangle(img, (x1_pixel, y1_pixel), (x2_pixel, y2_pixel), (0, 255, 0), 2)
            cv2.putText(img, f"{model.names[cls]} {conf:.2f}", (x1_pixel, y1_pixel - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.circle(img, (int(center_x_pixel), int(center_y_pixel)), 5, (0, 0, 255), -1)

    # Save the image with bounding boxes and IK results
    output_path = image_path.replace(".jpg", "_bbox_ik_results.jpg")
    cv2.imwrite(output_path, img)
    print(f"Saved annotated image: {output_path}")

    # Always close the Bluetooth socket when done or if an error occurs
    if bt_sock:
        print("Closing Bluetooth socket.")
        bt_sock.close()
    print("Script finished.")