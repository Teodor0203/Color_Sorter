import cv2
import numpy as np
import time # Import time for picamera2 warm-up

# Import Picamera2
from picamera2 import Picamera2

def nothing(x):
    # Callback function for trackbars (does nothing)
    pass

def hsv_color_calibrator():
    # --- Initialize Picamera2 ---
    picam2 = Picamera2()
    
    # Configure the camera. A common resolution for live processing is 640x480 or 1280x720.
    # The "format": "BGR888" ensures OpenCV receives frames in BGR format directly.
    camera_config = picam2.create_preview_configuration(main={"size": (1280, 720), "format": "BGR888"})
    picam2.configure(camera_config)

    try:
        picam2.start()
        # Give the camera some time to warm up and adjust exposure
        time.sleep(2)

        cv2.namedWindow("HSV Color Adjuster")
        cv2.createTrackbar("H_min", "HSV Color Adjuster", 0, 179, nothing)
        cv2.createTrackbar("S_min", "HSV Color Adjuster", 0, 255, nothing)
        cv2.createTrackbar("V_min", "HSV Color Adjuster", 0, 255, nothing)
        cv2.createTrackbar("H_max", "HSV Color Adjuster", 179, 179, nothing)
        cv2.createTrackbar("S_max", "HSV Color Adjuster", 255, 255, nothing)
        cv2.createTrackbar("V_max", "HSV Color Adjuster", 255, 255, nothing)

        print("\n--- HSV Color Calibrator ---")
        print("1. Place your wooden block(s) in front of the camera.")
        print("2. Adjust the trackbars until only your blocks appear white in the 'Mask' window.")
        print("3. Note down the H_min, S_min, V_min, H_max, S_max, V_max values from the trackbars.")
        print("4. Press 'q' to quit.")
        print("--- IMPORTANT: A GUI window will open. Ensure XCB/Qt libraries are installed on RPi. ---")
        print("----------------------------\n")

        while True:
            # Capture frame from Picamera2 as a NumPy array (BGR format)
            frame = picam2.capture_array("main") # Use "main" stream name as configured

            if frame is None:
                print("Failed to grab frame. Exiting...")
                break

            # The original script had this flip. You might or might not need it depending
            # on your camera orientation and how picamera2 handles it.
            # If the image appears upside down, keep it. Otherwise, you can remove it.
            # frame = cv2.flip(frame, 0)
            
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            h_min = cv2.getTrackbarPos("H_min", "HSV Color Adjuster")
            s_min = cv2.getTrackbarPos("S_min", "HSV Color Adjuster")
            v_min = cv2.getTrackbarPos("V_min", "HSV Color Adjuster")
            h_max = cv2.getTrackbarPos("H_max", "HSV Color Adjuster")
            s_max = cv2.getTrackbarPos("S_max", "HSV Color Adjuster")
            v_max = cv2.getTrackbarPos("V_max", "HSV Color Adjuster")

            lower_bound = np.array([h_min, s_min, v_min])
            upper_bound = np.array([h_max, s_max, v_max])

            mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)
            
            result = cv2.bitwise_and(frame, frame, mask=mask)

            cv2.imshow("Original Frame", frame)
            cv2.imshow("Mask", mask)
            cv2.imshow("Masked Result", result)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        # Capture final values before exiting
        final_h_min = cv2.getTrackbarPos("H_min", "HSV Color Adjuster")
        final_s_min = cv2.getTrackbarPos("S_min", "HSV Color Adjuster")
        final_v_min = cv2.getTrackbarPos("V_min", "HSV Color Adjuster")
        final_h_max = cv2.getTrackbarPos("H_max", "HSV Color Adjuster")
        final_s_max = cv2.getTrackbarPos("S_max", "HSV Color Adjuster")
        final_v_max = cv2.getTrackbarPos("V_max", "HSV Color Adjuster")

    except Exception as e:
        print(f"An error occurred during script execution: {e}")
        final_h_min, final_s_min, final_v_min = 0, 0, 0
        final_h_max, final_s_max, final_v_max = 179, 255, 255
    finally:
        # --- Cleanup ---
        picam2.stop() # Stop the camera gracefully
        cv2.destroyAllWindows()
        print("\nHSV Calibration finished.")
        print(f"Final Bounds: Lower({final_h_min},{final_s_min},{final_v_min}), Upper({final_h_max},{final_s_max},{final_v_max})")

if __name__ == "__main__":
    hsv_color_calibrator()
