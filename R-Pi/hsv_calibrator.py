import cv2
import numpy as np

def nothing(x):
    pass

def hsv_color_calibrator():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        print("Please ensure your webcam is connected and not in use by another application.")
        return

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
    print("----------------------------\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame. Exiting...")
            break

        frame = cv2.flip(frame, 0)
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

    cap.release()
    cv2.destroyAllWindows()
    print("\nHSV Calibration finished.")
    print(f"Final Bounds: Lower({h_min},{s_min},{v_min}), Upper({h_max},{s_max},{v_max})")

if __name__ == "__main__":
    hsv_color_calibrator()