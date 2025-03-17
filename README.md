# ELP Camera Control

Python package to control IMX179 ELP USB cameras using OpenCV. Supports video preview, recording with Unix timestamps, and multiple resolution modes.

## Features

- Automatic ELP USB camera detection
- Live video preview
- Video recording with Unix timestamp filenames
- Multiple resolution modes support
- Support for MJPEG and YUY2 video formats
- Command-line interface
- Synchronization-friendly (Unix timestamp filenames)

## Installation

1. Create and activate a virtual environment:

```bash
# On Linux/Mac
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate
```

2. Clone the repository and install the package:

```bash
git clone <repository-url>
cd elp-camera

# Create __init__.py if it doesn't exist
mkdir -p elp_camera
touch elp_camera/__init__.py

pip install -e .
```

## Usage

The package provides a command-line interface with several commands. The recommended way to use the camera is through a configuration file.

### Important: Camera Selection

For Mac users, the ELP camera is typically found at camera index 1:
- Camera index 0: Built-in MacBook FaceTime camera
- Camera index 1: ELP USB Camera (or iPhone/Continuity Camera)
- Camera index 2: Other external cameras (if available)

Always use `--camera-index 1` to ensure the ELP camera is selected.

### List Available Cameras

```bash
elp-camera list-devices
```

### List Available Resolutions

```bash
elp-camera list-resolutions
```

### Preview Camera Feed

```bash
elp-camera preview --camera-index 1 --resolution-index 1
```

For preview, you can use:
- Resolution index 1 (4656x3496) for highest quality preview (~9.5 FPS)
- Resolution index 11 (1920x1080) for faster preview (~19 FPS)

### Record Video

```bash
elp-camera record --camera-index 1 --resolution-index 11
```

For recording, use resolution index 11 (1920x1080 @ ~13 FPS) which has been confirmed to work reliably.

### Configuration File

The `camera_config.yaml` file contains settings that can be used to avoid typing parameters:

```yaml
camera_id: 1  # ELP Camera (important!)
resolution_index: 11  # 1920x1080 for reliable recording
video_format: "MJPEG"
output_dir: recordings
```

Use the config file with:

```bash
elp-camera record --config camera_config.yaml
```

## Troubleshooting

1. If the wrong camera is selected, explicitly specify camera index 1:
   ```bash
   elp-camera record --camera-index 1 --resolution-index 11
   ```

2. If auto-detection fails, make sure the ELP camera is properly connected via USB.

3. For optimal performance:
   - Use resolution index 11 (1920x1080) for recording
   - Higher resolution modes may work for preview but can be unstable for recording
   - If you experience issues, disconnect and reconnect the camera

4. The actual FPS is typically lower than advertised:
   - Resolution 11 (1920x1080): ~13-19 FPS (advertised as 30 FPS)
   - Resolution 1 (4656x3496): ~9.5 FPS (advertised as 1 FPS)

### Resolution Options

Available resolution indices:

- 0: 3264x2448 @ 15fps
- 1: 2592x1944 @ 20fps
- 2: 2048x1536 @ 20fps
- 3: 1600x1200 @ 20fps
- 4: 1280x960 @ 20fps
- 5: 1024x768 @ 30fps
- 6: 800x600 @ 30fps
- 7: 640x480 @ 30fps

### Video Formats

The camera supports two video formats:

- **MJPEG (Motion JPEG)**
  - Compressed format
  - Smaller file sizes
  - Higher compression ratio

- **YUY2 (YUYV, YUV422)**
  - Uncompressed format
  - Larger file sizes
  - Raw pixel data

### Controls

- Press 'q' to quit preview or recording mode
- Videos are saved in AVI format

## Requirements

- Python 3.6+
- OpenCV
- Click
- NumPy
- PyYAML
- libusb1
