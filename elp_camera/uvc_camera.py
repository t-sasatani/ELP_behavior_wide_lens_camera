import time
import cv2
import os
from typing import Optional, List, Dict


class ELPUVCCamera:
    # ELP-specific identifiers
    VENDOR_ID = 0x32E4
    PRODUCT_ID = 0x0298  # Updated to match your camera model

    # Resolution formats based on the specifications
    RESOLUTIONS = [
        {"width": 4656, "height": 3496, "format": "MJPEG", "fps": 10},
        {"width": 4656, "height": 3496, "format": "YUY2", "fps": 1},
        {"width": 4208, "height": 3120, "format": "MJPEG", "fps": 10},
        {"width": 4208, "height": 3120, "format": "YUY2", "fps": 1},
        {"width": 4160, "height": 3120, "format": "MJPEG", "fps": 10},
        {"width": 4000, "height": 3000, "format": "MJPEG", "fps": 10},
        {"width": 3840, "height": 2160, "format": "MJPEG", "fps": 10},
        {"width": 3264, "height": 2448, "format": "MJPEG", "fps": 10},
        {"width": 2592, "height": 1944, "format": "MJPEG", "fps": 10},
        {"width": 2320, "height": 1744, "format": "MJPEG", "fps": 30},
        {"width": 2048, "height": 1536, "format": "MJPEG", "fps": 30},
        {"width": 1920, "height": 1080, "format": "MJPEG", "fps": 30},
        {"width": 1600, "height": 1200, "format": "MJPEG", "fps": 30},
        {"width": 1280, "height": 960, "format": "MJPEG", "fps": 30},
        {"width": 1280, "height": 720, "format": "MJPEG", "fps": 30},
        {"width": 1024, "height": 768, "format": "MJPEG", "fps": 30},
        {"width": 800, "height": 600, "format": "MJPEG", "fps": 30},
        {"width": 640, "height": 480, "format": "MJPEG", "fps": 30},
    ]

    def __init__(self, camera_index=None):
        """Initialize the camera with optional index"""
        self.camera_index = camera_index
        self.cap = None
        self.current_format = None
        self.current_resolution = None
        self.recording = False

    @staticmethod
    def list_devices() -> List[Dict]:
        """List available cameras"""
        devices = []

        # Check first few camera indices (typically 0-9)
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Get initial frame to check if camera works
                    ret, frame = cap.read()
                    if ret:
                        # Get camera details
                        width = frame.shape[1]
                        height = frame.shape[0]

                        # Try to set a high resolution to identify potential ELP cameras
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2048)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1536)

                        high_res = False
                        ret2, frame2 = cap.read()
                        if ret2:
                            if frame2.shape[1] >= 1920 and frame2.shape[0] >= 1080:
                                high_res = True

                        # On macOS, typically:
                        # Camera 0 is built-in FaceTime camera
                        # Camera 1 is often iPhone or external webcam
                        # Camera 2+ are other devices

                        # We'll provide a hint about what each camera might be
                        camera_type = "Unknown"
                        is_elp = False

                        if i == 0:
                            camera_type = "Built-in FaceTime Camera"
                        elif i == 1:
                            camera_type = "External Camera (possibly iPhone)"
                        elif i == 2:
                            camera_type = "External Camera (possibly ELP)"
                            # We'll default to camera 2 being the ELP if it exists
                            is_elp = True

                        devices.append(
                            {
                                "index": i,
                                "name": f"{camera_type} ({width}x{height})"
                                + (" - High Resolution" if high_res else ""),
                                "is_elp": is_elp,
                                "vendor_id": ELPUVCCamera.VENDOR_ID if is_elp else 0,
                                "product_id": ELPUVCCamera.PRODUCT_ID if is_elp else 0,
                            }
                        )
                    cap.release()
            except Exception as e:
                print(f"Error checking camera {i}: {str(e)}")
                continue

        return devices

    def find_elp_camera_index(self) -> Optional[int]:
        """Find the camera index for the ELP camera using OpenCV"""
        print("Searching for ELP camera...")

        # CHECK IF CAMERA 2 IS AVAILABLE - ALWAYS PRIORITIZE IT
        print("Checking for ELP camera at index 2...")
        cap = cv2.VideoCapture(2)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(
                    f"Found ELP camera at index 2 ({frame.shape[1]}x{frame.shape[0]})"
                )
                cap.release()
                return 2
            cap.release()

        # Only fall back to other cameras if camera 2 is not available
        print(
            "Camera at index 2 not available or not working, checking other cameras..."
        )
        print(
            "Warning: Auto-detection may not work correctly. Please use --camera-index 2 explicitly."
        )

        # Default to camera index 2 if available on macOS (most likely the ELP camera)
        # Camera 0 is usually built-in, Camera 1 is usually iPhone Continuity Camera
        print("Checking available cameras...")
        for i in range(3):  # On macOS, typically limited to indices 0-2
            if i == 2:  # Skip 2, we already checked it
                continue
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(
                        f"Found working camera at index {i} ({frame.shape[1]}x{frame.shape[0]})"
                    )
                cap.release()

        # If we don't have camera 2, we need to check the available ones
        # Recommend camera 0 only if it's the only one available
        devices = self.list_devices()
        if len(devices) == 1:
            print(
                f"Only one camera available at index {devices[0]['index']}, but it's likely not the ELP camera."
            )
            print("Please ensure the ELP camera is connected and try again.")
            return None

        # If we have more than one camera, assume camera 1 might be the ELP
        # (since camera 0 is typically built-in)
        if len(devices) > 1:
            # Look for non-built-in cameras (indices other than 0)
            external_indices = [dev["index"] for dev in devices if dev["index"] != 0]
            if external_indices:
                print(
                    f"Found external camera at index {external_indices[0]}, but it may not be the ELP camera."
                )
                print("Please verify or specify --camera-index 2 explicitly.")
                return None

        print(
            "No ELP camera found. Please specify the camera index manually with --camera-index 2."
        )
        return None

    def open(
        self,
        resolution_index: int = 11,
        force_camera_index: bool = False,
        recording_mode: bool = False,
    ):  # Default to 1920x1080 (index 11) which is confirmed working
        """Open the camera with specified resolution

        Args:
            resolution_index: Index in the RESOLUTIONS array
            force_camera_index: Whether to skip auto-detection
            recording_mode: True if we're planning to record (may restrict resolution options)
        """
        if resolution_index < 0 or resolution_index >= len(self.RESOLUTIONS):
            print(f"Invalid resolution index: {resolution_index}")
            return False

        # If in recording mode, recommend resolution 11 (1920x1080) which is confirmed working
        if recording_mode and resolution_index != 11:
            print(
                f"Resolution index {resolution_index} may not work reliably for recording."
            )
            print("Resolution index 11 (1920x1080) is recommended for recording.")

        # Find the ELP camera if not specified
        if self.camera_index is None and not force_camera_index:
            print("Camera index not specified, auto-detecting...")
            self.camera_index = self.find_elp_camera_index()
            if self.camera_index is None:
                print(
                    "Failed to auto-detect ELP camera. Please try again with --camera-index"
                )
                return False
        else:
            print(f"Using specified camera index: {self.camera_index}")

        # Reset any existing camera
        self.close()

        try:
            print(f"Opening camera at index {self.camera_index}")
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                print(f"Failed to open camera at index {self.camera_index}")
                return False

            # Get the resolution settings
            res = self.RESOLUTIONS[resolution_index]
            print(
                f"Setting resolution to {res['width']}x{res['height']} @ {res['fps']}fps ({res['format']})"
            )

            # Take a test frame before changing settings to verify camera works
            ret, before_frame = self.cap.read()
            if ret:
                print(
                    f"Camera is working. Initial frame: {before_frame.shape[1]}x{before_frame.shape[0]}"
                )
            else:
                print("Warning: Could not get initial test frame")
                self.close()
                return False

            # Set format using fourcc
            if res["format"] == "MJPEG":
                fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            else:  # YUY2
                fourcc = cv2.VideoWriter_fourcc(*"YUY2")

            # Set properties - do this in a specific order for better compatibility
            self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            self.cap.set(cv2.CAP_PROP_FPS, res["fps"])
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, res["width"])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, res["height"])

            # Verify the settings were applied
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

            print(
                f"Actual resolution: {actual_width}x{actual_height} @ {actual_fps}fps"
            )

            # Take a test frame
            print("Taking test frame with new settings...")
            ret, frame = self.cap.read()
            if ret:
                print(f"Test frame size: {frame.shape[1]}x{frame.shape[0]}")
                self.current_resolution = (actual_width, actual_height, actual_fps)
                self.current_format = res["format"]

                # If the test frame doesn't match what we requested, use what we actually got
                if frame.shape[1] != actual_width or frame.shape[0] != actual_height:
                    print(
                        f"Note: Actual frame size ({frame.shape[1]}x{frame.shape[0]}) "
                        f"differs from reported settings ({actual_width}x{actual_height})"
                    )
                    self.current_resolution = (
                        frame.shape[1],
                        frame.shape[0],
                        actual_fps,
                    )

                # If recording mode, take a few more frames to ensure buffer is stable
                if recording_mode:
                    print("Testing recording stability...")
                    stable = True
                    for _ in range(5):  # Test with 5 consecutive frames
                        ret, _ = self.cap.read()
                        if not ret:
                            stable = False
                            break

                    if not stable:
                        print(
                            "Warning: Camera is not stable for recording at this resolution"
                        )
                        print(
                            "Try resolution index 11 (1920x1080) which is known to work"
                        )
                        self.close()
                        return False

                return True
            else:
                print("Failed to capture test frame")
                self.close()
                return False

        except Exception as e:
            print(f"Error opening camera: {str(e)}")
            self.close()
            return False

    def close(self):
        """Close the camera"""
        if self.cap:
            self.cap.release()
            self.cap = None

    def get_frame(self):
        """Get a frame from the camera"""
        if not self.cap:
            print("Camera not open")
            return False, None

        return self.cap.read()

    def preview(self):
        """Preview camera feed"""
        if not self.cap:
            print("Camera not open")
            return

        print("Starting preview - press 'q' to quit")
        frames_shown = 0
        start_time = time.time()

        try:
            while True:
                ret, frame = self.get_frame()
                if ret:
                    frames_shown += 1
                    cv2.imshow("Preview", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                    # Calculate FPS every ~30 frames
                    if frames_shown % 30 == 0:
                        elapsed = time.time() - start_time
                        fps = frames_shown / elapsed
                        print(f"Preview FPS: {fps:.2f}")
                else:
                    print("Failed to get frame")
                    time.sleep(0.1)

        finally:
            cv2.destroyAllWindows()
            elapsed = time.time() - start_time
            if frames_shown > 0 and elapsed > 0:
                print(f"Average FPS: {frames_shown / elapsed:.2f}")

    def record(self, output_dir: str):
        """Record video to file"""
        if not self.cap:
            print("Camera not open")
            return

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Create video writer
        timestamp = int(time.time())
        filename = os.path.join(output_dir, f"{timestamp}.avi")

        width, height, fps = self.current_resolution

        # Use codec based on current format
        if self.current_format == "MJPEG":
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        else:  # YUY2
            fourcc = cv2.VideoWriter_fourcc(*"YUY2")

        writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))

        if not writer.isOpened():
            print("Failed to create video writer")
            return

        print(f"Recording to {filename}")
        print(f"Resolution: {width}x{height} @ {fps}fps")
        print(f"Format: {self.current_format}")
        print("Press 'q' to stop recording")

        frames_written = 0
        start_time = time.time()

        try:
            while True:
                ret, frame = self.get_frame()
                if ret:
                    writer.write(frame)
                    frames_written += 1

                    # Update stats every ~30 frames
                    if frames_written % 30 == 0:
                        elapsed = time.time() - start_time
                        fps_actual = frames_written / elapsed
                        print(
                            f"Recorded {frames_written} frames ({fps_actual:.2f} FPS)"
                        )

                    # Show preview
                    cv2.imshow("Recording", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                else:
                    print("Failed to get frame")
                    time.sleep(0.1)

        finally:
            writer.release()
            cv2.destroyAllWindows()
            elapsed = time.time() - start_time
            if frames_written > 0 and elapsed > 0:
                print(f"Saved recording to {filename}")
                print(f"Recorded {frames_written} frames in {elapsed:.2f} seconds")
                print(f"Average FPS: {frames_written / elapsed:.2f}")
