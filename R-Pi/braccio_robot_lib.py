import numpy as np

class BraccioKinematicsSolver:
    def __init__(self):
        # --- Robot Link Lengths (MEASURE YOUR ROBOT CAREFULLY!) ---
        # L0: Height from base rotation axis to shoulder joint pivot
        self.L0 = 71.5 # Example: Height of the base servo block

        # L1: Length of the shoulder joint to elbow joint
        self.L1 = 125.0 # mm

        # L2: Length of the elbow joint to wrist vertical joint
        self.L2 = 125.0 # mm

        # L3: Length from wrist vertical joint to the gripper's end point
        self.L3 = 192.0 # mm

        print("\n--- Braccio Kinematics Solver Initialized ---")
        print("!!! WARNING: Please ensure LINK_LENGTHS_MM in braccio_robot_lib.py are accurate for YOUR Braccio robot. !!!")
        print(f"L0 (Base Height): {self.L0} mm")
        print(f"L1 (Bicep): {self.L1} mm")
        print(f"L2 (Forearm): {self.L2} mm")
        print(f"L3 (Gripper Offset): {self.L3} mm")
        print("-------------------------------------------\n")

    def calculate_joint_angles(self, target_x_mm, target_y_mm, target_z_mm):
        x = float(target_x_mm)
        y = float(target_y_mm)
        z = float(target_z_mm)

        if x == 0 or y == 0:
            return None
            
        # --- 1. Calculate Base (Waist) Angle (Servo 0) ---
        base_angle_rad = np.arctan2(y, x)
        base_angle_deg = np.degrees(base_angle_rad)

        # Adjust angle to Braccio's servo range (typically 0-180, 90 is center/forward)
        # Assuming 90 deg for straight forward, 0 for left, 180 for right.
        base_servo_angle = 90 - base_angle_deg # Example mapping
        if not (0 <= base_servo_angle <= 180):
            print(f"WARNING: Base angle {base_servo_angle:.1f}deg out of typical 0-180 range. Clamping.")
            base_servo_angle = np.clip(base_servo_angle, 0, 180)


        # --- 2. Calculate Effective Target for Shoulder and Elbow (2D Planar Arm) ---
        # Horizontal distance from base pivot to target projection on X-Y plane
        R = np.sqrt(x**2 + y**2)

        z_eff = z + self.L3 - self.L0 # The target for the wrist joint (L3 is length from wrist to gripper tip)

        # Ensure R is positive to avoid issues with np.sqrt, handle if target is at base origin
        if R < 1e-6: # Very close to base center
            R = 0 # Treat as 0 to simplify
            if abs(z_eff) < 1e-6:
                print("WARNING: Target is at base origin. Robot configuration ambiguous.")
                
        # Total straight-line distance from shoulder joint to wrist_v joint
        D = np.sqrt(R**2 + z_eff**2) 

        # Check reachability
        if D > (self.L1 + self.L2 + 30) or D < (abs(self.L1 - self.L2) + 30):
            print(f"ERROR: Target ({x:.1f},{y:.1f},{z:.1f}) mm is unreachable. D={D:.1f} mm, Max Reach={self.L1 + self.L2:.1f} mm.")
            return None

        # --- 3. Calculate Shoulder and Elbow Angles using Law of Cosines ---

        # Angle at the elbow joint (between L1 and L2)
        try:
            cos_elbow_angle = (self.L1**2 + self.L2**2 - D**2) / (2 * self.L1 * self.L2)
            cos_elbow_angle = np.clip(cos_elbow_angle, -1.0, 1.0)
            elbow_angle_rad = np.arccos(cos_elbow_angle)
        except RuntimeWarning:
            print("WARNING: Arccos input out of range for elbow. Clamped.")
            return None 
        
        # Angle between L1 and D at the shoulder joint
        try:
            cos_shoulder_angle_D = (self.L1**2 + D**2 - self.L2**2) / (2 * self.L1 * D)
            cos_shoulder_angle_D = np.clip(cos_shoulder_angle_D, -1.0, 1.0)
            shoulder_angle_D_rad = np.arccos(cos_shoulder_angle_D)
        except RuntimeWarning:
            print("WARNING: Arccos input out of range for shoulder-D. Clamped.")
            return None

        # Angle of the line D with the horizontal (R-axis)
        alpha_rad = np.arctan2(z_eff, R)

        # Shoulder (Bicep) Angle (Servo 1)
        shoulder_angle_rad = alpha_rad + shoulder_angle_D_rad
        shoulder_angle_deg = np.degrees(shoulder_angle_rad)

        # Elbow (Forearm) Angle (Servo 2)
        # Assuming 0deg is fully extended and 180deg is fully bent.
        elbow_angle_deg = np.degrees(elbow_angle_rad) # This is the internal angle of the triangle at the elbow

        # --- 4. Map to Braccio Servo Angles (0-180 degrees) ---
        shoulder_servo_angle = shoulder_angle_deg - 5

        elbow_servo_angle = elbow_angle_deg - 90

        # --- 5. Apply Joint Limits (Braccio-specific limits) ---
        joint_limits = {
            'base': (0, 180),
            'shoulder': (15, 165),
            'elbow': (0, 180),    
        }

        base_servo_angle = np.clip(base_servo_angle, *joint_limits['base'])
        shoulder_servo_angle = np.clip(shoulder_servo_angle, *joint_limits['shoulder'])
        elbow_servo_angle = np.clip(elbow_servo_angle, *joint_limits['elbow'])

        angles = {
            'base': round(base_servo_angle, 1),
            'shoulder': round(shoulder_servo_angle, 1),
            'elbow': round(elbow_servo_angle, 1),
        }
        
        return angles

if __name__ == "__main__":
    solver = BraccioKinematicsSolver()

    print("\n--- Testing Braccio Kinematics Solver ---")
    
    # Target 1: A point forward and slightly to the side
    target_x = 180  # mm
    target_y = -100    # mm (straight forward)
    target_z = 0   # mm (50mm above base plane)
    print(f"\nTarget 1: X={target_x}mm, Y={target_y}mm, Z={target_z}mm")
    angles = solver.calculate_joint_angles(target_x, target_y, target_z)
    if angles:
        print("Calculated Angles:", angles)
    else:
        print("Target 1 is unreachable.")

    # Target 2: A point slightly to the side
    target_x = 150
    target_y = 100
    target_z = 20
    print(f"\nTarget 2: X={target_x}mm, Y={target_y}mm, Z={target_z}mm")
    angles = solver.calculate_joint_angles(target_x, target_y, target_z)
    if angles:
        print("Calculated Angles:", angles)
    else:
        print("Target 2 is unreachable.")

    # Target 3: An unreachable point (too far)
    target_x = 500
    target_y = 0
    target_z = 50
    print(f"\nTarget 3 (Unreachable): X={target_x}mm, Y={target_y}mm, Z={target_z}mm")
    angles = solver.calculate_joint_angles(target_x, target_y, target_z)
    if angles:
        print("Calculated Angles:", angles)
    else:
        print("Target 3 is unreachable.")

    # Target 4: A point below the base
    target_x = 100
    target_y = 0
    target_z = -20
    print(f"\nTarget 4: X={target_x}mm, Y={target_y}mm, Z={target_z}mm")
    angles = solver.calculate_joint_angles(target_x, target_y, target_z)
    if angles:
        print("Calculated Angles:", angles)
    else:
        print("Target 4 is unreachable (or calculation failed).")

    print("\nEnd of Braccio Kinematics Solver Test.")
