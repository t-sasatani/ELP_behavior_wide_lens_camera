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
- Camera restart capabilities for recovery from unstable states

## Installation

1. Create and activate a virtual environment:

```bash
# On Linux/Mac
python3 -m venv venv
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

For recording, use:
- Resolution index 11 (1920x1080 @ ~13 FPS) for better frame rate
- Resolution index 10 (2048x1536 @ ~9.3 FPS) for higher resolution

### Custom Resolution and FPS

Instead of using predefined resolution indices, you can set custom resolution and FPS values directly:

```bash
# First set a custom resolution
elp-camera set-resolution --camera-index 1 --width 2048 --height 1536

# Then set a custom frame rate
elp-camera set-fps --camera-index 1 --fps 15

# Finally, start recording
elp-camera record --camera-index 1
```

This allows for more precise control over camera settings than using the predefined resolution indices.

For stubborn cameras, add the --force flag to try multiple resolution-setting methods:

```bash
elp-camera set-resolution --camera-index 1 --width 2048 --height 1536 --force
```

### Camera Recovery When Resolutions Stop Working

If a resolution that previously worked stops working (often happens after switching formats or resolutions), use the camera restart command:

```bash
elp-camera restart-camera --camera-index 1 --hard-reset
```

This performs a thorough reset of the camera and can restore functionality to resolutions that have stopped working.

### Automatic Camera Recovery

If the camera gets into an unstable state (common after changing resolutions or formats), use the auto-restart flag:

```bash
elp-camera record --camera-index 1 --resolution-index 11 --auto-restart
```

This will attempt to restart the camera automatically if it fails to open. For more stubborn issues, add the hard reset option:

```bash
elp-camera record --camera-index 1 --resolution-index 11 --auto-restart --hard-reset
```

### Manual Camera Restart

You can also manually restart the camera if it's in a bad state:

```bash
elp-camera restart-camera --camera-index 1 --resolution-index 11
```

For more persistent issues, use the hard reset option:

```bash
elp-camera restart-camera --camera-index 1 --hard-reset
```

This is useful when:
- The camera is stuck after changing resolutions
- Preview or recording commands fail to open the camera
- After switching between YUY2 and MJPEG formats
- When a resolution that worked before suddenly stops working

### Configuration File

The `camera_config.yaml` file contains settings that can be used to avoid typing parameters:

```yaml
camera_id: 1  # ELP Camera (important!)
# Choose based on your needs:
resolution_index: 11  # 1920x1080 for faster FPS (~13 FPS)
# resolution_index: 10  # 2048x1536 for higher resolution (~9.3 FPS)
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
   - If you experience issues, use the `--auto-restart` flag or the `restart-camera` command
   - As a last resort, disconnect and reconnect the camera physically

4. The actual FPS is typically lower than advertised:
   - Resolution 11 (1920x1080): ~13-19 FPS (advertised as 30 FPS)
   - Resolution 10 (2048x1536): ~9.3 FPS (advertised as 30 FPS) 
   - Resolution 1 (4656x3496): ~9.5 FPS (advertised as 1 FPS)
   
5. Camera state issues:
   - **If a resolution suddenly stops working**: Use the restart command with hard reset
     ```bash
     elp-camera restart-camera --camera-index 1 --hard-reset
     ```
   - Switching between formats (MJPEG/YUY2) can cause instability
   - Changing between certain resolutions may require a camera restart
   - The camera reset feature can usually recover the camera without physical disconnection

### Camera Parameter Controls

The ELP camera supports adjusting various parameters using OpenCV. Use the following commands to view and modify camera settings:

#### List Available Camera Properties

```bash
elp-camera get-properties --camera-index 1
```

This command shows all available camera properties and their current values, along with whether each property is changeable on your specific camera.

> **Note for macOS Users**: Due to limitations in the macOS camera drivers, many standard camera properties like gain, exposure, and brightness may not be changeable through the standard OpenCV interfaces. The `get-properties` command will show you which properties can actually be changed on your system.

#### Set General Camera Property

```bash
elp-camera set-property --camera-index 1 --name PROPERTY_NAME --value VALUE
```

Replace `PROPERTY_NAME` with one of: BRIGHTNESS, CONTRAST, SATURATION, GAIN, etc.

For macOS users who find that standard properties don't work, try using direct property IDs:

```bash
elp-camera set-property --camera-index 1 --prop-id PROPERTY_ID --value VALUE
```

Where `PROPERTY_ID` is a numeric ID that may work with your specific camera driver. Common alternative IDs to try:
- 81: Alternative gain control
- 15, 4, 204: Alternative exposure controls
- 10: Alternative brightness control

#### Set Specific Parameters

1. **Gain Control**:
   ```bash
   elp-camera set-gain --camera-index 1 --gain 50
   ```
   Adjust gain values (typically 0-100) to control image brightness in low light.

2. **Exposure Control**:
   ```bash
   elp-camera set-exposure --camera-index 1 --exposure -1
   ```
   Set exposure value (negative values enable auto exposure).

3. **Auto Exposure Toggle**:
   ```bash
   elp-camera set-auto-exposure --camera-index 1 --auto
   ```
   Enable auto exposure, or use `--manual` to disable it.

4. **Brightness Control**:
   ```bash
   elp-camera set-brightness --camera-index 1 --brightness 80
   ```
   Adjust brightness values (typically 0-100).

5. **Height/Resolution Control (macOS)**:
   ```bash
   elp-camera set-height --camera-index 1 --height 1200
   ```
   Set the camera's vertical resolution (only confirmed working on macOS). Try values like 1200, 1300, 1500, or 1744.
   
   > **Note**: This command uses property ID 4, which appears to control the image height on ELP cameras with macOS. Generally, you can only set values higher than the current height (e.g., from 1080 to 1200).

6. **Frame Rate Control**:
   ```bash
   elp-camera set-fps --camera-index 1 --fps 15
   ```
   Set the camera's frame rate (FPS). Try values between 5-30 depending on your camera and resolution.
   
   > **Note**: This command uses property ID 5, which controls the frame rate. The actual achievable frame rate may be limited by your camera hardware, resolution, and USB bandwidth. The command will measure and report the actual frame rate achieved.

7. **Direct Resolution Setting**:
   ```bash
   # Try to set a specific resolution
   elp-camera set-resolution --camera-index 1 --width 1920 --height 1080
   
   # For stubborn cameras, try the force option to attempt multiple methods
   elp-camera set-resolution --camera-index 1 --width 1280 --height 720 --force
   
   # Example: Setting high resolution (2K)
   elp-camera set-resolution --camera-index 1 --width 2048 --height 1536
   
   # Example: Setting resolution and then FPS for recording
   elp-camera set-resolution --camera-index 1 --width 2048 --height 1536
   elp-camera set-fps --camera-index 1 --fps 15
   elp-camera record --camera-index 1
   ```
   This command attempts to set a custom resolution using multiple methods, useful when the predefined resolution indices don't provide what you need.

#### Troubleshooting Camera Properties

If you find that camera properties aren't changing despite using the commands above:

1. First check which properties are actually changeable on your system:
   ```bash
   elp-camera get-properties --camera-index 1
   ```

2. Look for the "Properties that can be changed on this camera" section in the output.

3. If no properties are listed as changeable, try using direct property IDs:
   ```bash
   elp-camera set-property --camera-index 1 --prop-id 4 --value 1200
   ```

4. Use the property scanner to find working IDs for your specific camera:
   ```bash
   # Scan property IDs from 0 to 100
   elp-camera scan-properties --camera-index 1
   
   # Focus on a specific property ID to test multiple values
   elp-camera scan-properties --camera-index 1 --focus-id 4
   
   # Scan a different range (e.g., 500-600 for some macOS cameras)
   elp-camera scan-properties --camera-index 1 --min-id 500 --max-id 600
   ```
   
   For a more comprehensive scan that checks for resolution changes and can scan a wider range:
   ```bash
   # Deep scan with default settings (IDs 0-600)
   elp-camera deep-scan-properties --camera-index 1
   
   # Faster scan by checking every 5th ID
   elp-camera deep-scan-properties --camera-index 1 --skip 5
   
   # Scan a specific range thoroughly
   elp-camera deep-scan-properties --camera-index 1 --min-id 200 --max-id 300
   ```
   
   These scans will systematically test each property ID and show you which ones actually work with your camera.

5. **Known Working Properties on macOS**:
   
   Our deep scan has identified the following working camera properties:
   
   - **Property ID 3**: Current width value (read-only)
   - **Property ID 4**: Current height value (can be changed)
   - **Property ID 5**: Current FPS value (can be changed)
   - **Property ID 8**: Unknown purpose, value is 16.0 (read-only)
   
   > **Important Note for macOS Users**: Many camera parameters like gain, exposure, and white balance cannot be controlled through OpenCV on macOS. For these parameters, we recommend using the 'Webcam Settings' app, which works well with ELP cameras. See the "Alternative Camera Control for macOS Users" section below for more details.
   
   **Height Control (Property ID 4)**:
   
   This property appears to control image height and can be adjusted to values like 1100, 1200, 1300, or 1744:
   
   ```bash
   # Try different values to adjust camera image height
   elp-camera set-property --camera-index 1 --prop-id 4 --value 1200
   
   # Or use the dedicated command
   elp-camera set-height --camera-index 1 --height 1200
   ```
   
   Note that setting this value lower than the current value (e.g., 1000 when it's at 1080) might not work, but setting it higher often does work.

   **Frame Rate Control (Property ID 5)**:
   
   This property controls the frame rate (FPS) and can be set to values like 5, 10, 15, or 30:
   
   ```bash
   # Try different values to adjust camera frame rate
   elp-camera set-property --camera-index 1 --prop-id 5 --value 15
   
   # Or use the dedicated command
   elp-camera set-fps --camera-index 1 --fps 15
   ```
   
   Note that the actual achievable frame rate may be limited by your camera hardware, resolution, and USB bandwidth.

6. If all else fails, you may need to use external lighting or positioning to control the brightness and exposure of your recordings, as macOS camera drivers often limit direct property control.

### Alternative Camera Control for macOS Users

While OpenCV on macOS has limitations for controlling camera parameters like gain, exposure, white balance, etc., there is a great alternative:

**Webcam Settings App**
- The 'Webcam Settings' app for macOS works well with ELP cameras
- It provides direct control over:
  - Gain
  - Exposure
  - White balance
  - Brightness
  - Contrast
  - And other camera parameters

This approach is often more reliable than trying to control these parameters through OpenCV, especially on macOS where camera driver interfaces have more restrictions. The settings applied through the 'Webcam Settings' app will persist while the camera is in use by this software.

You can use the 'Webcam Settings' app to adjust your camera before starting recording with the ELP Camera control commands.

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
  - More reliable for most operations

- **YUY2 (YUYV, YUV422)**
  - Uncompressed format
  - Larger file sizes
  - Raw pixel data
  - May cause instability when switching formats

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
