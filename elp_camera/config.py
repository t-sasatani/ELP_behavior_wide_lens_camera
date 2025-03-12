import yaml
from dataclasses import dataclass


@dataclass
class CameraConfig:
    camera_id: int = 1
    resolution_index: int = 7
    output_dir: str = "recordings"

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "CameraConfig":
        """Load configuration from YAML file"""
        with open(yaml_path, "r") as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)

    def to_yaml(self, yaml_path: str) -> None:
        """Save configuration to YAML file"""
        with open(yaml_path, "w") as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)
