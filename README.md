# ELP Camera Control

Python package to control IMX179 ELP USB cameras using OpenCV. Supports video preview, recording with Unix timestamps, and multiple resolution modes.

## Features

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

The package provides a command-line interface with two main commands:

### Preview Mode

To preview the camera feed:

```bash
elp-camera preview --camera-id 0 --resolution-index 0
```

Resolution indices:

- 0: 3264x2448 @ 15fps
- 1: 2592x1944 @ 20fps
- 2: 2048x1536 @ 20fps
- 3: 1600x1200 @ 20fps
- 4: 1280x960 @ 20fps
- 5: 1024x768 @ 30fps
- 6: 800x600 @ 30fps
- 7: 640x480 @ 30fps

### Recording Mode

To record video (with Unix timestamp filename):

```bash
elp-camera record --camera-id 0 --resolution-index 0 --output-dir recordings
```

The video will be saved in the specified output directory with a Unix timestamp as the filename (e.g., `1234567890.avi`).

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

You can specify the format in the config file:

```yaml
video_format: "MJPEG"  # or "YUY2"
```

### Controls

- Press 'q' to quit preview or recording mode
- Videos are saved in AVI format using XVID codec

## Requirements

- Python 3.6+
- OpenCV
- Click
- NumPy
