import cv2
import time
import os


class CameraRecorder:
    def __init__(self, camera, output_dir: str = "recordings"):
        self.camera = camera
        self.output_dir = output_dir
        self.writer = None
        self.recording = False
        self.current_filename = None

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def start_recording(self) -> bool:
        """Start recording with Unix timestamp filename"""
        if self.recording:
            return False

        if self.camera.cap is None:
            return False

        timestamp = int(time.time())
        resolution = self.camera.current_resolution
        if resolution is None:
            return False

        width, height, fps = resolution
        self.current_filename = f"{self.output_dir}/{timestamp}.avi"

        # Check if directory is writable
        if not os.access(self.output_dir, os.W_OK):
            print(f"Cannot write to directory: {self.output_dir}")
            return False

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.writer = cv2.VideoWriter(
            self.current_filename, fourcc, fps, (width, height)
        )

        if not self.writer.isOpened():
            print(f"Failed to create video writer for file: {self.current_filename}")
            return False

        self.recording = True
        return True

    def stop_recording(self) -> None:
        """Stop recording"""
        if self.writer is not None:
            self.writer.release()
            self.writer = None
        self.recording = False
        self.current_filename = None

    def record_frame(self, frame) -> bool:
        """Record a single frame"""
        if not self.recording or self.writer is None:
            return False

        self.writer.write(frame)
        return True
