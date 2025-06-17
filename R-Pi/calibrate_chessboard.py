import cv2
import numpy as np
import glob
import os

def calibrate_camera(image_folder, chessboard_size, square_size_mm):
    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
    objp = objp * square_size_mm

    objpoints = []
    imgpoints = []

    if not os.path.exists(image_folder):
        print(f"Error: Image folder '{image_folder}' not found.")
        print("Please create this folder and place your chessboard calibration images inside it.")
        return None, None

    images = glob.glob(image_folder + '/*.png')

    if not images:
        print(f"No images found in '{image_folder}'.")
        print("Please ensure you have captured and saved chessboard images in this folder.")
        return None, None

    print(f"Found {len(images)} images for calibration in '{image_folder}'.")
    print("Detecting chessboard corners (might open windows for each image)...")

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    for i, fname in enumerate(images):
        img = cv2.imread(fname)
        if img is None:
            print(f"Warning: Could not read image {fname}. Skipping.")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

        if ret == True:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)

            cv2.drawChessboardCorners(img, chessboard_size, corners2, ret)
            cv2.imshow(f'Image {i+1} - Corners Found', img)
            cv2.waitKey(100)
        else:
            print(f"Could not find chessboard corners in {fname}")
            cv2.imshow(f'Image {i+1} - No Corners Found', img)
            cv2.waitKey(100)

    cv2.destroyAllWindows()

    if not objpoints or not imgpoints:
        print("No valid chessboard corner sets found across all images. Calibration failed.")
        return None, None

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    if ret:
        print("\nCamera calibrated successfully!")
        print("Camera matrix (mtx):\n", mtx)
        print("Distortion coefficients (dist):\n", dist)

        mean_error = 0
        for i in range(len(objpoints)):
            imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
            error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2)/len(imgpoints2)
            mean_error += error
        print(f"Total reprojection error: {mean_error/len(objpoints):.4f} pixels (lower is better)")

        np.savez('camera_calibration.npz', mtx=mtx, dist=dist)
        print("Calibration data saved to camera_calibration.npz")

        return mtx, dist
    else:
        print("Camera calibration failed.")
        return None, None

if __name__ == "__main__":
    chessboard_size = (7, 6)
    square_size_mm = 23.0 # IMPORTANT

    image_folder = 'calibration_images'
    
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
        print(f"Created folder: {image_folder}")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera for image capture.")
    else:
        print("\n--- Image Capture for Calibration ---")
        print(f"Press 's' to save a frame to '{image_folder}'. Press 'q' to quit.")
        img_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame during capture.")
                break
            
            display_frame = frame.copy()
            cv2.putText(display_frame, f"Saved: {img_count} | Press 's' to save, 'q' to quit", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Capture for Calibration', display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                file_path = os.path.join(image_folder, f'calib_img_{img_count:03d}.png')
                cv2.imwrite(file_path, frame)
                print(f"Saved {file_path}")
                img_count += 1
            elif key == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        print("Image capture finished.")

    # --- Actual calibration ---
    print("\n--- Starting Camera Calibration Process ---")
    camera_matrix, dist_coeffs = calibrate_camera(image_folder, chessboard_size, square_size_mm)

    if camera_matrix is not None:
        print("\nCamera calibration data (camera_matrix.npz) is ready for use with ArUco detection.")