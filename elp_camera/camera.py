import cv2
import numpy as np
from typing import Tuple, Optional


class ELPCamera:
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

    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.cap = None
        self.current_resolution = None
        self.recording = False

    def open(self) -> bool:
        """Open the camera connection"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"Failed to open camera {self.camera_id}")
            raise RuntimeError("Failed to open camera")
        return True

    def close(self) -> None:
        """Close the camera connection"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def set_resolution(self, width: int, height: int, fps: int) -> bool:
        """Set camera resolution and fps"""
        if self.cap is None:
            print("Cannot set resolution: camera not initialized")
            return False

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

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Capture a single frame"""
        if self.cap is None:
            print("Camera not initialized")
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            print(f"Failed to read frame from camera {self.camera_id}")
        return ret, frame

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

    @staticmethod
    def list_cameras() -> list:
        """List available cameras"""
        available_cameras = []
        for i in range(10):  # Check first 10 indexes
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        return available_cameras
