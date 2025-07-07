import cv2
import numpy as np
import glob
import os
import time # Import time for Picamera2 delays

# Import Picamera2
from picamera2 import Picamera2, Preview

def calibrate_camera(image_folder, chessboard_size, square_size_mm):
    """
    Performs camera calibration using chessboard images.
    
    Args:
        image_folder (str): Path to the folder containing chessboard images.
        chessboard_size (tuple): Number of inner corners (width, height) on the chessboard (e.g., (7, 6)).
        square_size_mm (float): Size of a single square on the chessboard in millimeters.
    
    Returns:
        tuple: (camera_matrix, distortion_coefficients) if calibration is successful,
               otherwise (None, None).
    """
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
    objp = objp * square_size_mm

    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.

    if not os.path.exists(image_folder):
        print(f"Error: Image folder '{image_folder}' not found.")
        print("Please create this folder and place your chessboard calibration images inside it.")
        return None, None

    images = glob.glob(image_folder + '/*.png') # Get list of PNG images

    if not images:
        print(f"No images found in '{image_folder}'.")
        print("Please ensure you have captured and saved chessboard images in this folder.")
        return None, None

    print(f"Found {len(images)} images for calibration in '{image_folder}'.")
    print("Detecting chessboard corners (might open windows for each image)...")

    # Criteria for corner refinement
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # Placeholder for the last valid grayscale image shape for calibrateCamera
    last_gray_shape = None

    for i, fname in enumerate(images):
        img = cv2.imread(fname)
        if img is None:
            print(f"Warning: Could not read image {fname}. Skipping.")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        last_gray_shape = gray.shape[::-1] # Store shape for calibration
        
        # Find the chessboard corners
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)

            # Draw and display the corners
            cv2.drawChessboardCorners(img, chessboard_size, corners2, ret)
            # Ensure you have XCB/Qt libraries installed for cv2.imshow on RPi if running with GUI
            # If not, this part will cause an error like "Could not load the Qt platform plugin xcb"
            cv2.imshow(f'Image {i+1} - Corners Found', img)
            cv2.waitKey(100) # Display for 100ms
        else:
            print(f"Could not find chessboard corners in {fname}")
            cv2.imshow(f'Image {i+1} - No Corners Found', img)
            cv2.waitKey(100)

    cv2.destroyAllWindows() # Close all OpenCV windows

    if not objpoints or not imgpoints:
        print("No valid chessboard corner sets found across all images. Calibration failed.")
        return None, None
    
    if last_gray_shape is None:
        print("Error: No valid images were processed to determine camera resolution for calibration.")
        return None, None

    # Perform camera calibration
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, last_gray_shape, None, None)

    if ret:
        print("\nCamera calibrated successfully!")
        print("Camera matrix (mtx):\n", mtx)
        print("Distortion coefficients (dist):\n", dist)

        # Calculate reprojection error
        mean_error = 0
        for i in range(len(objpoints)):
            imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
            error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2)/len(imgpoints2)
            mean_error += error
        print(f"Total reprojection error: {mean_error/len(objpoints):.4f} pixels (lower is better)")

        # Save calibration data
        np.savez('camera_calibration.npz', mtx=mtx, dist=dist)
        print("Calibration data saved to camera_calibration.npz")

        return mtx, dist
    else:
        print("Camera calibration failed.")
        return None, None

if __name__ == "__main__":
    chessboard_size = (7, 6) # Number of inner corners (width, height)
    square_size_mm = 23.0 # IMPORTANT: Measure your physical chessboard square size in millimeters

    image_folder = 'calibration_images'
    
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
        print(f"Created folder: {image_folder}")

    # --- Initialize Picamera2 ---
    picam2 = Picamera2()
    # Configure for a good resolution for calibration images.
    # For calibration, it's recommended to use the highest resolution you'll use for your application.
    # The 'main' stream is for high-res capture, 'lores' for lower-res preview.
    camera_config = picam2.create_still_configuration(
        main={"size": (1280, 720), "format": "BGR888"}, # High-res capture for calibration, BGR format
        lores={"size": (640, 480)}, # Low-res for display preview (if enabled)
        display="lores" # Display the lores stream
    )
    picam2.configure(camera_config)

    try:
        picam2.start()
        # Give the camera some time to warm up and adjust exposure
        time.sleep(2)
        
        print("\n--- Image Capture for Calibration (using Pi Camera) ---")
        print(f"Press 's' to save a frame to '{image_folder}'. Press 'q' to quit.")
        img_count = 0
        while True:
            # Capture frame from Picamera2's main stream as a NumPy array (BGR format)
            frame = picam2.capture_array("main")
            fliped_frame = cv2.flip(frame, 1)

            if frame is None:
                print("Failed to grab frame during capture.")
                break
            
            # display_frame = fliped_frame.copy()
            cv2.putText(frame, f"Saved: {img_count} | Press 's' to save, 'q' to quit", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # If you are running this on a desktop environment with a display:
            # Ensure you have XCB/Qt libraries installed for cv2.imshow
            # (e.g., sudo apt install libgl1-mesa-glx libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libqt5core5a libqt5gui5 libqt5widgets5)
            cv2.imshow('Capture for Calibration', frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                file_path = os.path.join(image_folder, f'calib_img_{img_count:03d}.png')
                cv2.imwrite(file_path, frame)
                print(f"Saved {file_path}")
                img_count += 1
                time.sleep(0.5) # Add a small delay after saving to avoid rapid captures
            elif key == ord('q'):
                break
        
        print("Image capture finished.")

    finally:
        # --- Clean up Picamera2 ---
        picam2.stop() # Stop the camera gracefully
        cv2.destroyAllWindows() # Close any remaining OpenCV windows

    # --- Actual calibration ---
    print("\n--- Starting Camera Calibration Process ---")
    camera_matrix, dist_coeffs = calibrate_camera(image_folder, chessboard_size, square_size_mm)

    if camera_matrix is not None:
        print("\nCamera calibration data (camera_calibration.npz) is ready for use with ArUco detection.")
