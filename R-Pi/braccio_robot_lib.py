import numpy as np

class BraccioKinematicsSolver:
    def __init__(self):
        self.L0 = 71.5 # base height
        self.L1 = 125.0 # shoulder length
        self.L2 = 125.0 # elbow lenght
        self.L3 = 192.0 # wrist length

        print("\n--- Braccio Kinematics Solver Initialized ---")
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
            
        # --- 1. Calculate Base Angle (M0) ---
        base_angle_rad = np.arctan2(y, x)
        base_angle_deg = np.degrees(base_angle_rad)

        base_servo_angle = 90 - base_angle_deg

        if not (0 <= base_servo_angle <= 180):
            print(f"WARNING: Base angle {base_servo_angle:.1f}deg out of typical 0-180 range. Clamping.")
            base_servo_angle = np.clip(base_servo_angle, 0, 180)

        # if base_servo_angle < 80:
        #     base_servo_angle += 10
        # else:
        #     base_servo_angle -= 10


        # --- 2. Calculate Effective Target for Shoulder and Elbow (2D Planar Arm) ---
        # Horizontal distance from base to target projection on X-Y plane
        R = np.sqrt(x**2 + y**2)

        z_eff = z + self.L3 - self.L0 # The target for the wrist joint (L3 is length from wrist to gripper tip)

        if R < 1e-6: # Very close to base center
            R = 0 # Treat as 0 to simplify
            if abs(z_eff) < 1e-6:
                print("WARNING: Target is at base origin. Robot configuration ambiguous.")
                
        # Total straight-line distance from shoulder joint to wrist_v joint
        D = np.sqrt(R**2 + z_eff**2) 

        # Check if in reach
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

        # Angle of the line D with the horizontal
        alpha_rad = np.arctan2(z_eff, R)

        # Shoulder Angle (M1)
        shoulder_angle_rad = alpha_rad + shoulder_angle_D_rad
        shoulder_angle_deg = np.degrees(shoulder_angle_rad)

        # Elbow Angle (M2)
        elbow_angle_deg = np.degrees(elbow_angle_rad)

        # --- 4. Map to Braccio Servo Angles ---
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