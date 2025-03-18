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
        self.current_resolution_index = (
            None  # Track current resolution index for restart
        )
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

        # Store the resolution index for restart purposes
        self.current_resolution_index = resolution_index

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

    def restart(self, resolution_index=None, recording_mode=False, hard_reset=False):
        """Restart the camera by closing and reopening it

        Args:
            resolution_index: Optional new resolution index. If None, use the current one.
            recording_mode: True if planning to record (affects resolution validation)
            hard_reset: If True, perform a more thorough reset by trying multiple close/reopen cycles

        Returns:
            bool: True if restart was successful, False otherwise
        """
        print("Restarting camera...")

        # Save camera state
        saved_camera_index = self.camera_index

        # Determine resolution to use
        if resolution_index is None and self.current_resolution_index is not None:
            resolution_index = self.current_resolution_index
        elif resolution_index is None:
            # Default to 1920x1080 if no resolution specified
            resolution_index = 11

        print(
            f"Will restart camera at index {saved_camera_index} with resolution index {resolution_index}"
        )

        # Close the camera completely
        self.close()

        # Wait for resources to be released
        time.sleep(1)

        # For hard reset, try releasing and reopening multiple times to clear any USB buffer issues
        if hard_reset:
            print("Performing hard reset sequence...")
            # Try multiple open/close cycles with different resolutions to reset internal camera state
            temp_resolutions = [17, 11]  # Try low resolution first, then higher
            for temp_res in temp_resolutions:
                print(f"Reset cycle with temporary resolution {temp_res}...")
                # Try to open with a simple resolution
                temp_cap = cv2.VideoCapture(saved_camera_index)
                if temp_cap.isOpened():
                    # Set some basic properties
                    temp_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    temp_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    # Read a frame
                    ret, _ = temp_cap.read()
                    print(f"  Temporary open result: {'Success' if ret else 'Failed'}")
                    # Close it
                    temp_cap.release()
                    time.sleep(1)

        # Try to reopen multiple times
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"Restart attempt {attempt}/{max_attempts}...")

            # Re-initialize
            self.camera_index = saved_camera_index

            # For stubborn cameras, try opening with a known good resolution first (640x480)
            if hard_reset and attempt > 1:
                print("Trying intermediate resolution first...")
                temp_cap = cv2.VideoCapture(saved_camera_index)
                if temp_cap.isOpened():
                    temp_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    temp_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    temp_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
                    ret, _ = temp_cap.read()
                    temp_cap.release()
                    time.sleep(1)

            # Open with the saved or new resolution
            success = self.open(
                resolution_index, force_camera_index=True, recording_mode=recording_mode
            )

            if success:
                print("Camera restarted successfully")
                return True

            # Wait before retrying
            if attempt < max_attempts:
                print("Restart failed, waiting before retry...")
                time.sleep(2)

        # If all attempts failed, suggest trying a known good resolution
        if resolution_index != 11:
            print(
                "All restart attempts failed. Trying one last time with resolution index 11 (1920x1080)..."
            )
            success = self.open(
                11, force_camera_index=True, recording_mode=recording_mode
            )
            if success:
                print("Camera restarted successfully with resolution index 11")
                print("Please use this resolution for reliable operation")
                return True

        print("Failed to restart camera after multiple attempts")
        print("Try physically disconnecting and reconnecting the camera")
        return False

    def get_camera_properties(self):
        """Get all available camera properties and their current values"""
        if not self.cap or not self.cap.isOpened():
            print("Camera not open")
            return {}

        # Common camera properties in OpenCV
        properties = {
            "CAP_PROP_BRIGHTNESS": cv2.CAP_PROP_BRIGHTNESS,
            "CAP_PROP_CONTRAST": cv2.CAP_PROP_CONTRAST,
            "CAP_PROP_SATURATION": cv2.CAP_PROP_SATURATION,
            "CAP_PROP_HUE": cv2.CAP_PROP_HUE,
            "CAP_PROP_GAIN": cv2.CAP_PROP_GAIN,
            "CAP_PROP_EXPOSURE": cv2.CAP_PROP_EXPOSURE,
            "CAP_PROP_AUTO_EXPOSURE": cv2.CAP_PROP_AUTO_EXPOSURE,
            "CAP_PROP_GAMMA": cv2.CAP_PROP_GAMMA,
            "CAP_PROP_BACKLIGHT": cv2.CAP_PROP_BACKLIGHT,
            "CAP_PROP_TEMPERATURE": cv2.CAP_PROP_TEMPERATURE,
            "CAP_PROP_ZOOM": cv2.CAP_PROP_ZOOM,
            "CAP_PROP_FOCUS": cv2.CAP_PROP_FOCUS,
            "CAP_PROP_AUTOFOCUS": cv2.CAP_PROP_AUTOFOCUS,
            "CAP_PROP_SHARPNESS": cv2.CAP_PROP_SHARPNESS,
        }

        # Additional properties to check (may work on some cameras)
        extended_properties = {
            # Additional IDs that might be used by some cameras/drivers
            "CAP_PROP_GAIN_ALT": 81,  # Alternative gain property
            "CAP_PROP_EXPOSURE_ALT1": 15,  # Alternative exposure property
            "CAP_PROP_EXPOSURE_ALT2": 4,
            "CAP_PROP_EXPOSURE_ALT3": 204,
            "CAP_PROP_AUTO_EXPOSURE_ALT1": 21,
            "CAP_PROP_AUTO_EXPOSURE_ALT2": 39,
            "CAP_PROP_AUTO_EXPOSURE_ALT3": 1024,
        }

        # Get current values
        current_values = {}
        # Check standard properties
        for name, prop_id in properties.items():
            value = self.cap.get(prop_id)
            current_values[name] = value

        # Also check extended properties
        for name, prop_id in extended_properties.items():
            value = self.cap.get(prop_id)
            # Only include non-zero values to reduce clutter
            if abs(value) > 0.01:
                current_values[name] = value

        # Include changeable status
        print("\nTesting which properties can be changed:")
        for name, prop_id in properties.items():
            initial = self.cap.get(prop_id)
            # Try to set a different value
            test_value = 10 if abs(initial) < 1 else initial + 5

            # Save current frame to allow camera to stabilize after change
            ret, _ = self.cap.read()

            if self.cap.set(prop_id, test_value):
                # Read a frame to refresh camera state
                ret, _ = self.cap.read()
                new_value = self.cap.get(prop_id)
                changed = abs(new_value - initial) > 0.01

                # Restore original value
                self.cap.set(prop_id, initial)
                # Read a frame to refresh camera state
                ret, _ = self.cap.read()

                current_values[f"{name}_CHANGEABLE"] = "YES" if changed else "NO"
            else:
                current_values[f"{name}_CHANGEABLE"] = "NO"

        return current_values

    def set_camera_property(self, prop_name, value):
        """Set a camera property by name

        Args:
            prop_name: Property name (e.g., "GAIN", "EXPOSURE", "BRIGHTNESS")
            value: The value to set

        Returns:
            bool: True if property was set successfully, False otherwise
        """
        if not self.cap or not self.cap.isOpened():
            print("Camera not open")
            return False

        # Map property names to OpenCV constants
        property_map = {
            "BRIGHTNESS": cv2.CAP_PROP_BRIGHTNESS,
            "CONTRAST": cv2.CAP_PROP_CONTRAST,
            "SATURATION": cv2.CAP_PROP_SATURATION,
            "HUE": cv2.CAP_PROP_HUE,
            "GAIN": cv2.CAP_PROP_GAIN,
            "EXPOSURE": cv2.CAP_PROP_EXPOSURE,
            "AUTO_EXPOSURE": cv2.CAP_PROP_AUTO_EXPOSURE,
            "GAMMA": cv2.CAP_PROP_GAMMA,
            "BACKLIGHT": cv2.CAP_PROP_BACKLIGHT,
            "TEMPERATURE": cv2.CAP_PROP_TEMPERATURE,
            "ZOOM": cv2.CAP_PROP_ZOOM,
            "FOCUS": cv2.CAP_PROP_FOCUS,
            "AUTOFOCUS": cv2.CAP_PROP_AUTOFOCUS,
            "SHARPNESS": cv2.CAP_PROP_SHARPNESS,
        }

        # Alternative property IDs - some cameras use different IDs for the same properties
        alternative_property_map = {
            # Known alternatives for different camera drivers/backends
            "BRIGHTNESS": [10, 1, 101],
            "CONTRAST": [11, 2, 102],
            "SATURATION": [12, 3, 103],
            "HUE": [13, 4, 104],
            "GAIN": [
                14,
                5,
                105,
                81,
            ],  # 81 is an alternative gain control on some cameras
            "EXPOSURE": [15, 6, 106, 4, 204],  # Multiple alternatives for exposure
            "AUTO_EXPOSURE": [16, 21, 39, 1024],  # Different auto exposure controls
        }

        # Find the property ID
        prop_name = prop_name.upper()
        if prop_name not in property_map:
            print(f"Unknown property: {prop_name}")
            return False

        prop_id = property_map[prop_name]

        # Get initial value for comparison
        initial_value = self.cap.get(prop_id)
        print(f"Initial {prop_name} value: {initial_value}")

        # Try to set the property using standard ID
        print(f"Attempting to set {prop_name} ({prop_id}) to {value}")
        result = self.cap.set(prop_id, value)

        # Verify if value changed
        new_value = self.cap.get(prop_id)
        print(f"After set attempt - {prop_name} value: {new_value}")

        if (
            result and abs(new_value - value) < 0.1
        ):  # Allow small floating point difference
            print(f"Successfully set {prop_name} to {new_value}")
            return True
        else:
            print("Standard property ID failed, trying alternative IDs")

            # Try alternative property IDs if the standard one failed
            if prop_name in alternative_property_map:
                for alt_id in alternative_property_map[prop_name]:
                    print(f"Trying alternative ID {alt_id} for {prop_name}")
                    alt_initial = self.cap.get(alt_id)
                    print(f"  Current value with ID {alt_id}: {alt_initial}")

                    # Try setting with alternative ID
                    alt_result = self.cap.set(alt_id, value)
                    alt_new = self.cap.get(alt_id)
                    print(f"  After set attempt - value with ID {alt_id}: {alt_new}")

                    if alt_result and abs(alt_new - alt_initial) > 0.01:
                        print(
                            f"Successfully set {prop_name} using alternative ID {alt_id}"
                        )
                        return True

            print(f"Failed to set {prop_name} to {value} (no change detected)")

            # For exposure specifically, we'll try setting auto exposure modes as well
            if prop_name == "EXPOSURE":
                print("Trying to disable auto exposure first...")
                # Try different auto exposure modes (0 is often manual, 1 is auto, 3 is another auto mode)
                auto_exp_ids = [cv2.CAP_PROP_AUTO_EXPOSURE, 21, 39, 1024]
                for auto_id in auto_exp_ids:
                    print(f"  Setting auto exposure ID {auto_id} to 0 (manual mode)")
                    self.cap.set(auto_id, 0)

                # Try setting exposure again
                print(f"  Retrying exposure ({prop_id}) with auto exposure disabled")
                retry_result = self.cap.set(prop_id, value)
                retry_value = self.cap.get(prop_id)
                print(f"  After retry - {prop_name} value: {retry_value}")

                if retry_result and abs(retry_value - initial_value) > 0.01:
                    print(f"Successfully set {prop_name} after disabling auto exposure")
                    return True

            return False

    def set_gain(self, gain_value):
        """Set camera gain

        Args:
            gain_value: Gain value (typically 0-100)

        Returns:
            bool: True if successful, False otherwise
        """
        return self.set_camera_property("GAIN", gain_value)

    def set_exposure(self, exposure_value):
        """Set camera exposure

        Args:
            exposure_value: Exposure value (negative values for auto exposure)

        Returns:
            bool: True if successful, False otherwise
        """
        return self.set_camera_property("EXPOSURE", exposure_value)

    def set_auto_exposure(self, auto_exposure):
        """Set auto exposure mode

        Args:
            auto_exposure: 0 for manual, 1 for auto (may vary by camera)

        Returns:
            bool: True if successful, False otherwise
        """
        return self.set_camera_property("AUTO_EXPOSURE", auto_exposure)

    def set_brightness(self, brightness_value):
        """Set camera brightness

        Args:
            brightness_value: Brightness value (typically 0-100)

        Returns:
            bool: True if successful, False otherwise
        """
        return self.set_camera_property("BRIGHTNESS", brightness_value)

    def set_fps(self, fps_value):
        """Set camera frames per second (FPS)

        Args:
            fps_value: FPS value to set (typically 5-30)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.cap or not self.cap.isOpened():
            print("Camera not open")
            return False

        FPS_PROP_ID = 5  # Property ID 5 corresponds to FPS in OpenCV

        # Get initial value for comparison
        initial_fps = self.cap.get(FPS_PROP_ID)
        print(f"Initial FPS value: {initial_fps}")

        # Try to set the FPS
        print(f"Attempting to set FPS to {fps_value}")
        result = self.cap.set(FPS_PROP_ID, fps_value)

        # Take a few frames to apply the change
        for _ in range(3):
            ret, _ = self.cap.read()

        # Check if it worked
        new_fps = self.cap.get(FPS_PROP_ID)
        print(f"After set attempt - FPS value: {new_fps}")

        if result and abs(new_fps - initial_fps) > 0.01:
            print(f"Successfully set FPS to {new_fps}")
            return True
        else:
            print(f"Failed to set FPS to {fps_value} (no change detected)")
            return False
