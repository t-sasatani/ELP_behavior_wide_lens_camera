import cv2
import numpy as np
import usb1
from typing import Tuple, Optional, Dict


class ELPCamera:
    # Video format options
    VIDEO_FORMATS = {
        "MJPEG": cv2.VideoWriter_fourcc(*"MJPG"),
        "YUY2": cv2.VideoWriter_fourcc(*"YUY2"),
    }

    RESOLUTIONS = [
        (3264, 2448, 15),  # 15fps
        (2592, 1944, 20),  # 20fps
        (2048, 1536, 20),  # 20fps
        (1600, 1200, 20),  # 20fps
        (1280, 960, 20),  # 20fps
        (1024, 768, 30),  # 30fps
        (800, 600, 30),  # 30fps
        (640, 480, 30),  # 30fps
    ]

    # ELP-specific identifiers
    VENDOR_ID = 0x32E4
    PRODUCT_ID = 0x0298  # Updated to match your actual ELP camera

    @staticmethod
    def find_elp_camera_id() -> Optional[int]:
        """Find the camera ID for the ELP USB camera"""
        # First, find the USB device
        context = usb1.USBContext()

        # List all USB devices for debugging
        print("Searching for ELP camera...")
        found_elp = False
        elp_bus = None
        elp_address = None

        for device in context.getDeviceList():
            vid = device.getVendorID()
            pid = device.getProductID()
            bus = device.getBusNumber()
            addr = device.getDeviceAddress()
            print(
                f"Found USB device: VID=0x{vid:04x}, PID=0x{pid:04x}, Bus={bus}, Addr={addr}"
            )

            if vid == ELPCamera.VENDOR_ID and pid == ELPCamera.PRODUCT_ID:
                print(f"Found matching ELP USB device on Bus {bus}, Address {addr}!")
                found_elp = True
                elp_bus = bus
                elp_address = addr

        if not found_elp:
            print(
                f"No USB device found with VID=0x{ELPCamera.VENDOR_ID:04x}, PID=0x{ELPCamera.PRODUCT_ID:04x}"
            )
            return None

        # Now find which OpenCV camera index corresponds to our ELP camera
        print("\nChecking video devices...")

        # Try each camera index
        for i in range(3):  # On macOS, we're limited to indices 0-2
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"\nTesting camera {i}...")

                # First check current resolution
                ret, frame = cap.read()
                if ret:
                    print(f"Initial resolution: {frame.shape[1]}x{frame.shape[0]}")

                    # Try setting different resolutions
                    for res_idx, (width, height, fps) in enumerate(
                        ELPCamera.RESOLUTIONS
                    ):
                        print(f"Testing resolution {width}x{height}...")
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                        cap.set(cv2.CAP_PROP_FPS, fps)

                        # Read a frame to verify
                        ret, frame = cap.read()
                        if ret:
                            actual_width = frame.shape[1]
                            actual_height = frame.shape[0]
                            print(f"Got resolution: {actual_width}x{actual_height}")

                            # If camera supports our high resolutions (>2000 pixels), it's likely our ELP
                            if actual_width >= 2000 and actual_height >= 1500:
                                print(
                                    f"Found ELP camera at index {i} (verified with {actual_width}x{actual_height})"
                                )
                                cap.release()
                                return i

                cap.release()

        print("No matching video device found for ELP camera")
        return None

    @staticmethod
    def list_cameras() -> Dict[int, dict]:
        """List available cameras with details"""
        available_cameras = {}
        elp_id = ELPCamera.find_elp_camera_id()

        # On macOS, we're limited to indices 0-2
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    resolution = f"{frame.shape[1]}x{frame.shape[0]}"
                else:
                    resolution = "unknown"
                is_elp = i == elp_id
                available_cameras[i] = {"resolution": resolution, "is_elp": is_elp}
                cap.release()
        return available_cameras

    def __init__(self, camera_id: Optional[int] = None):
        """Initialize camera with optional ID, otherwise find ELP camera automatically"""
        if camera_id is None:
            camera_id = self.find_elp_camera_id()
            if camera_id is None:
                raise RuntimeError("Could not find ELP camera")
        self.camera_id = camera_id
        self.cap = None
        self.current_resolution = None
        self.current_format = None
        self.recording = False

    def open(self) -> bool:
        """Open the camera connection"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"Failed to open camera {self.camera_id}")
            raise RuntimeError("Failed to open camera")

        # Take a test frame to verify camera is working
        ret, frame = self.cap.read()
        if not ret:
            print("Warning: Could not read initial frame")
        else:
            print(
                f"Camera opened successfully, initial frame: {frame.shape[1]}x{frame.shape[0]}"
            )
        return True

    def close(self) -> None:
        """Close the camera connection"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def set_resolution(self, resolution_index: int) -> bool:
        """Set camera resolution and fps based on resolution index"""
        if not 0 <= resolution_index < len(self.RESOLUTIONS):
            print(f"Invalid resolution index: {resolution_index}")
            return False

        if self.cap is None:
            print("Cannot set resolution: camera not initialized")
            return False

        width, height, fps = self.RESOLUTIONS[resolution_index]
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)

        # Verify settings were applied
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        print(f"Requested: {width}x{height} @ {fps}fps")
        print(f"Actual: {actual_width}x{actual_height} @ {actual_fps}fps")

        self.current_resolution = (
            int(actual_width),
            int(actual_height),
            int(actual_fps),
        )
        return True

    def set_format(self, format_name: str) -> bool:
        """Set video format (MJPEG or YUY2)"""
        if format_name not in self.VIDEO_FORMATS:
            print(f"Unsupported format: {format_name}. Use MJPEG or YUY2")
            return False

        if self.cap is None:
            print("Camera not initialized")
            return False

        fourcc = self.VIDEO_FORMATS[format_name]
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        self.current_format = format_name
        print(f"Set video format to {format_name}")
        return True

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Capture a single frame"""
        if self.cap is None:
            print("Camera not initialized")
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            print(f"Failed to read frame from camera {self.camera_id}")
        return ret, frame

    def record(self, output_dir: str) -> None:
        """Record video with Unix timestamp filename"""
        import time
        import os

        if self.cap is None:
            print("Camera not initialized")
            return

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Create video writer with Unix timestamp filename
        timestamp = int(time.time())
        filename = os.path.join(output_dir, f"{timestamp}.avi")

        # Get current resolution
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))

        # Get current format
        fourcc = self.VIDEO_FORMATS.get(
            self.current_format, cv2.VideoWriter_fourcc(*"MJPG")
        )

        writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        if not writer.isOpened():
            raise RuntimeError(
                f"Failed to create video writer with format {self.current_format}"
            )

        print(f"Recording to {filename}")
        print(f"Resolution: {width}x{height} @ {fps}fps")
        print(f"Format: {self.current_format}")
        print("Press 'q' to stop recording")

        self.recording = True
        frames_written = 0
        try:
            while self.recording:
                ret, frame = self.get_frame()
                if ret:
                    writer.write(frame)
                    frames_written += 1
                    # Show preview
                    cv2.imshow("Recording", frame)
                    # Check for 'q' key to stop recording
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                else:
                    print("Failed to get frame, retrying...")
                    # Try reinitializing the camera
                    self.close()
                    self.open()
                    if self.current_format:
                        self.set_format(self.current_format)
                    if self.current_resolution:
                        width, height, fps = self.current_resolution
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                        self.cap.set(cv2.CAP_PROP_FPS, fps)
                    continue
        finally:
            writer.release()
            cv2.destroyAllWindows()
            print(f"Saved recording to {filename} ({frames_written} frames written)")

    def get_current_settings(self) -> dict:
        """Get current camera settings"""
        if self.cap is None:
            return {}

        return {
            "resolution": self.current_resolution,
            "brightness": self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            "contrast": self.cap.get(cv2.CAP_PROP_CONTRAST),
            "saturation": self.cap.get(cv2.CAP_PROP_SATURATION),
            "gain": self.cap.get(cv2.CAP_PROP_GAIN),
        }
