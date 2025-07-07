import cv2
import cv2.aruco as aruco
import numpy as np
import os

class ObjectDetector:
    def __init__(self, calibration_file, aruco_dict_type, marker_length_mm, color_ranges, min_object_area_pixels):
        self.calibration_file = calibration_file
        self.aruco_dict_type = aruco_dict_type
        self.marker_length_mm = marker_length_mm
        self.color_ranges = color_ranges
        self.min_object_area_pixels = min_object_area_pixels

        self.camera_matrix = None
        self.dist_coeffs = None
        self.aruco_dict = None
        self.aruco_parameters = None
        self.aruco_detector = None

        self._load_camera_calibration()
        self._initialize_aruco_detector()

        print(f"Marker Length: {self.marker_length_mm} mm")
        print(f"Detecting colors: {', '.join(self.color_ranges.keys())}")


    def _load_camera_calibration(self):
        try:
            if os.path.exists(self.calibration_file):
                calib_data = np.load(self.calibration_file)
                self.camera_matrix = calib_data['mtx']
                self.dist_coeffs = calib_data['dist']
                print(f"Loaded camera calibration data from {self.calibration_file}.")
            else:
                raise FileNotFoundError(f"Calibration file '{self.calibration_file}' not found.")
        except Exception as e:
            print(f"ERROR: Failed to load camera calibration data: {e}")
            raise

    def _initialize_aruco_detector(self):
        self.aruco_dict = aruco.getPredefinedDictionary(self.aruco_dict_type)
        self.aruco_parameters = aruco.DetectorParameters()
        self.aruco_detector = aruco.ArucoDetector(self.aruco_dict, self.aruco_parameters)

    def _get_3d_coordinates_on_plane(self, pixel_coords, rvec_plane, tvec_plane):
        u, v = pixel_coords
        
        try:
            undistorted_points = cv2.undistortPoints(
                np.array([[u, v]], dtype=np.float32), 
                self.camera_matrix, 
                self.dist_coeffs, 
                P=self.camera_matrix
            )
            undistorted_u, undistorted_v = undistorted_points[0][0]

            R_plane, _ = cv2.Rodrigues(rvec_plane)
            normal_in_plane_frame = np.array([[0], [0], [1]], dtype=np.float32)
            normal_in_camera_frame = R_plane @ normal_in_plane_frame
            normal_in_camera_frame = normal_in_camera_frame.flatten()

            point_on_plane_in_camera_frame = tvec_plane.flatten()

            ray_direction = np.linalg.inv(self.camera_matrix) @ np.array([[undistorted_u], [undistorted_v], [1.0]])
            ray_direction = ray_direction.flatten()

            dot_product_numerator = np.dot(normal_in_camera_frame, point_on_plane_in_camera_frame)
            dot_product_denominator = np.dot(normal_in_camera_frame, ray_direction)

            if abs(dot_product_denominator) < 1e-6:
                return None

            t = dot_product_numerator / dot_product_denominator
            point_3d_camera_frame = t * ray_direction

            return point_3d_camera_frame
        except Exception as e:
            print(f"DEBUG: Error in _get_3d_coordinates_on_plane: {e}")
            return None

    def process_frame(self, frame):
        # Undistort the frame using the loaded camera calibration
        undistorted_frame = cv2.undistort(frame, self.camera_matrix, self.dist_coeffs, None, self.camera_matrix)
        display_frame = undistorted_frame.copy()

        gray_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2GRAY)
        hsv_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2HSV)

        # Initialize return values
        aruco_data = None
        detected_objects = []

        # --- ArUco Marker Detection and Pose Estimation ---
        marker_tvec = None
        marker_rvec = None
        marker_px_center = None
        
        corners, ids, rejectedImgPoints = self.aruco_detector.detectMarkers(gray_frame)

        if ids is not None and len(ids) > 0:
            index = 0
            single_corner = corners[index]
            detected_marker_id = ids[index][0]

            try:
                rvec, tvec, _ = aruco.estimatePoseSingleMarkers(single_corner, self.marker_length_mm, self.camera_matrix, self.dist_coeffs)
                marker_rvec = rvec[0]
                marker_tvec = tvec[0]

                cv2.drawFrameAxes(display_frame, self.camera_matrix, self.dist_coeffs, marker_rvec, marker_tvec, self.marker_length_mm / 2)

                marker_origin_3d = np.array([[0.0, 0.0, 0.0]])
                marker_projected_points, _ = cv2.projectPoints(marker_origin_3d, marker_rvec, marker_tvec, self.camera_matrix, self.dist_coeffs)
                marker_px_center = (int(marker_projected_points[0][0][0]), int(marker_projected_points[0][0][1]))

                # Display ArUco ID and its Z-distance from camera
                cv2.putText(display_frame, f"ArUco ID: {detected_marker_id}", (int(single_corner[0][0][0]), int(single_corner[0][0][1]) - 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(display_frame, f"Marker Z: {marker_tvec[0][2]:.2f} mm",
                            (int(single_corner[0][0][0]), int(single_corner[0][0][1]) + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                
                # Draw a circle at the projected marker center for visual verification
                cv2.circle(display_frame, marker_px_center, 7, (0, 255, 255), -1)

                aruco_data = {
                    'rvec': marker_rvec,
                    'tvec': marker_tvec,
                    'px_center': marker_px_center,
                    'id': detected_marker_id
                }

            except Exception as e:
                cv2.putText(display_frame, "ArUco Pose Error!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            cv2.putText(display_frame, "No ArUco Markers Found!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)


        # --- Color-Based Object Detection ---
        objects_count = 0
        for color_name, bounds in self.color_ranges.items():
            lower_bound = bounds["lower"]
            upper_bound = bounds["upper"]

            mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)
            
            kernel = np.ones((5,5),np.uint8)
            mask = cv2.erode(mask, kernel, iterations=1)
            mask = cv2.dilate(mask, kernel, iterations=2)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > self.min_object_area_pixels:
                    objects_count += 1
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        cv2.circle(display_frame, (cx, cy), 5, (0, 0, 255), -1)

                        cv2.putText(display_frame, f"{color_name}", (x, y - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                        
                        rel_px_from_aruco = None
                        rel_3d_from_aruco_mm = None

                        if aruco_data is not None:
                            # Pixel Coordinates relative to ArUco Marker's Center
                            rel_px_x = cx - aruco_data['px_center'][0]
                            rel_px_y = cy - aruco_data['px_center'][1]
                            rel_px_from_aruco = (rel_px_x, rel_px_y)
                            cv2.putText(display_frame, f"Rel Px: ({rel_px_x},{rel_px_y})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                            # Estimate 3D Coordinates relative to ArUco Marker's Origin
                            object_3d_camera_frame = self._get_3d_coordinates_on_plane(
                                (cx, cy), aruco_data['rvec'], aruco_data['tvec']
                            )

                            if object_3d_camera_frame is not None:
                                R_marker_to_cam, _ = cv2.Rodrigues(aruco_data['rvec'])
                                R_cam_to_marker = R_marker_to_cam.T
                                T_cam_to_marker = -R_cam_to_marker @ aruco_data['tvec'].reshape(3,1)

                                object_3d_marker_frame = R_cam_to_marker @ object_3d_camera_frame.reshape(3,1) + T_cam_to_marker
                                
                                Y_mm = -object_3d_marker_frame[0][0]
                                X_mm = object_3d_marker_frame[1][0]
                                Z_mm = object_3d_marker_frame[2][0]
                                rel_3d_from_aruco_mm = (X_mm, Y_mm, Z_mm)

                                cv2.putText(display_frame, f"3D Rel Marker (mm):", (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                                cv2.putText(display_frame, f"X:{X_mm:.0f} Y:{Y_mm:.0f} Z:{Z_mm:.0f}",
                                            (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                            else:
                                cv2.putText(display_frame, "3D Est: Calcfail", (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                        else:
                            cv2.putText(display_frame, "Rel Px: No Marker", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            cv2.putText(display_frame, "3D Est: NoMarkerPose", (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                        
                        detected_objects.append({
                            'color_name': color_name,
                            'bbox': (x, y, w, h),
                            'centroid_px': (cx, cy),
                            'rel_px_from_aruco': rel_px_from_aruco,
                            'rel_3d_from_aruco_mm': rel_3d_from_aruco_mm
                        })

        if objects_count == 0 and aruco_data is None:
            cv2.putText(display_frame, "No Objects Detected", (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return display_frame, aruco_data, detected_objects