import yaml
import os
from typing import Optional, Dict, Any


class CameraConfig:
    def __init__(
        self,
        camera_id: Optional[int] = None,
        resolution_index: int = 17,
        video_format: str = "MJPEG",
        output_dir: str = "recordings",
    ):
        """Initialize camera configuration"""
        self.camera_id = camera_id
        self.resolution_index = resolution_index
        self.video_format = video_format
        self.output_dir = output_dir

    @classmethod
    def from_yaml(cls, file_path: str) -> "CameraConfig":
        """Load configuration from YAML file"""
        if not os.path.exists(file_path):
            print(f"Config file not found: {file_path}")
            return cls()

        try:
            with open(file_path, "r") as f:
                config_data = yaml.safe_load(f)

            # Handle config_data being None (empty file)
            if config_data is None:
                config_data = {}

            # Print the loaded configuration for debugging
            print(f"Loaded configuration from {file_path}:")
            for key, value in config_data.items():
                print(f"  {key}: {value}")

            return cls(
                camera_id=config_data.get("camera_id"),
                resolution_index=config_data.get("resolution_index", 17),
                video_format=config_data.get("video_format", "MJPEG"),
                output_dir=config_data.get("output_dir", "recordings"),
            )
        except Exception as e:
            print(f"Error loading config from {file_path}: {str(e)}")
            return cls()

    def to_yaml(self, file_path: str) -> bool:
        """Save configuration to YAML file"""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Convert to dictionary
            config_data = {
                "camera_id": self.camera_id,
                "resolution_index": self.resolution_index,
                "video_format": self.video_format,
                "output_dir": self.output_dir,
            }

            # Remove None values
            config_data = {k: v for k, v in config_data.items() if v is not None}

            with open(file_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)

            return True
        except Exception as e:
            print(f"Error saving config to {file_path}: {str(e)}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "camera_id": self.camera_id,
            "resolution_index": self.resolution_index,
            "video_format": self.video_format,
            "output_dir": self.output_dir,
        }
