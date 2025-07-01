import click
import os
import cv2
import time
from .uvc_camera import ELPUVCCamera
from .config import CameraConfig


@click.group()
def cli():
    """ELP camera control CLI with UVC support"""
    pass


@cli.command()
def list_devices():
    """List available cameras"""
    devices = ELPUVCCamera.list_devices()
    if devices:
        click.echo("Found cameras:")
        for dev in devices:
            elp_status = " (ELP USB Camera)" if dev["is_elp"] else ""
            click.echo(f"Camera {dev['index']}: {dev['name']}{elp_status}")
    else:
        click.echo("No cameras found")


@cli.command()
@click.option(
    "--resolution-index",
    default=17,
    help="Resolution index (0-17, see list-resolutions)",
)
@click.option(
    "--camera-index",
    type=int,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option("--config", type=str, help="Path to YAML configuration file")
@click.option(
    "--auto-restart", is_flag=True, help="Automatically restart camera if it fails"
)
@click.option(
    "--hard-reset",
    is_flag=True,
    help="Perform a more thorough reset if auto-restart is enabled",
)
def preview(resolution_index, camera_index, config, auto_restart, hard_reset):
    """Preview camera feed"""
    if config and os.path.exists(config):
        camera_config = CameraConfig.from_yaml(config)
        resolution_index = getattr(camera_config, "resolution_index", resolution_index)
        if camera_index is None and hasattr(camera_config, "camera_id"):
            camera_index = getattr(camera_config, "camera_id")

    camera = ELPUVCCamera(camera_index)
    try:
        force_camera = camera_index is not None
        success = camera.open(resolution_index, force_camera_index=force_camera)

        # Handle camera failure with auto-restart
        if not success and auto_restart:
            click.echo("Initial camera open failed. Attempting to restart...")
            if hard_reset:
                click.echo("Using thorough reset sequence...")
            success = camera.restart(resolution_index, hard_reset=hard_reset)

        if success:
            camera.preview()
        else:
            click.echo(
                "Failed to open camera. Try specifying --camera-index 1 and --resolution-index 11, "
                "or use --auto-restart --hard-reset to attempt recovery."
            )
    finally:
        camera.close()


@cli.command()
@click.option(
    "--resolution-index",
    default=11,  # Default to 1920x1080 which is confirmed working for recording
    help="Resolution index (0-17, see list-resolutions)",
)
@click.option(
    "--camera-index",
    type=int,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option(
    "--output-dir", default="recordings", help="Output directory for recordings"
)
@click.option("--config", type=str, help="Path to YAML configuration file")
@click.option(
    "--auto-restart", is_flag=True, help="Automatically restart camera if it fails"
)
@click.option(
    "--hard-reset",
    is_flag=True,
    help="Perform a more thorough reset if auto-restart is enabled",
)
def record(
    resolution_index, camera_index, output_dir, config, auto_restart, hard_reset
):
    """Record video with Unix timestamp filename"""
    if config and os.path.exists(config):
        camera_config = CameraConfig.from_yaml(config)
        resolution_index = getattr(camera_config, "resolution_index", resolution_index)
        output_dir = getattr(camera_config, "output_dir", output_dir)
        if camera_index is None and hasattr(camera_config, "camera_id"):
            camera_index = getattr(camera_config, "camera_id")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    camera = ELPUVCCamera(camera_index)
    try:
        force_camera = camera_index is not None
        success = camera.open(
            resolution_index, force_camera_index=force_camera, recording_mode=True
        )

        # Handle camera failure with auto-restart
        if not success and auto_restart:
            click.echo("Initial camera open failed. Attempting to restart...")
            if hard_reset:
                click.echo("Using thorough reset sequence...")
            success = camera.restart(
                resolution_index, recording_mode=True, hard_reset=hard_reset
            )

        if success:
            camera.record(output_dir)
        else:
            click.echo(
                "Failed to open camera. Try specifying --camera-index 1 and --resolution-index 11, "
                "or use --auto-restart --hard-reset to attempt recovery."
            )
    finally:
        camera.close()


@cli.command()
def list_resolutions():
    """List available resolutions for the ELP camera"""
    click.echo("Available resolutions for ELP camera:")
    camera = ELPUVCCamera()
    for i, res in enumerate(camera.RESOLUTIONS):
        click.echo(
            f"{i}: {res['width']}x{res['height']} @ {res['fps']}fps ({res['format']})"
        )


@cli.command()
@click.option("--camera-index", type=int, required=True, help="Camera index to restart")
@click.option(
    "--resolution-index",
    type=int,
    help="Resolution index to use after restart (uses previous if not specified)",
)
@click.option(
    "--hard-reset",
    is_flag=True,
    help="Perform a more thorough reset for stubborn camera issues",
)
def restart_camera(camera_index, resolution_index, hard_reset):
    """Manually restart a camera that may be in a bad state"""
    if hard_reset:
        click.echo(f"Attempting thorough reset of camera at index {camera_index}...")
    else:
        click.echo(f"Attempting to restart camera at index {camera_index}...")

    camera = ELPUVCCamera(camera_index)
    success = camera.restart(resolution_index, hard_reset=hard_reset)

    if success:
        click.echo("Camera restart successful!")
        click.echo(
            "Camera is now ready for use. You can now run preview or record commands."
        )
    else:
        click.echo("Camera restart failed.")
        if not hard_reset:
            click.echo("Try using --hard-reset option for more thorough reset.")
        click.echo(
            "If that fails, try physically disconnecting and reconnecting the camera."
        )

    camera.close()


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
def get_properties(camera_index):
    """Get all available camera properties and their values"""
    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            props = camera.get_camera_properties()
            click.echo("Camera properties:")
            # Group properties for better readability
            standard_props = {}
            changeable_status = {}
            alternative_props = {}

            for name, value in props.items():
                if "_CHANGEABLE" in name:
                    changeable_status[name.replace("_CHANGEABLE", "")] = value
                elif "_ALT" in name:
                    alternative_props[name] = value
                else:
                    standard_props[name] = value

            # Display standard properties with changeable status
            click.echo("\nStandard OpenCV properties:")
            for name, value in standard_props.items():
                status = changeable_status.get(name, "UNKNOWN")
                click.echo(f"  {name}: {value} [Changeable: {status}]")

            # Display alternative properties if any
            if alternative_props:
                click.echo("\nAlternative property IDs (may work on some cameras):")
                for name, value in alternative_props.items():
                    click.echo(f"  {name}: {value}")

            # Provide a summary of what can be changed
            changeable_props = [
                name for name, status in changeable_status.items() if status == "YES"
            ]
            if changeable_props:
                click.echo(
                    f"\nProperties that can be changed on this camera: {', '.join(changeable_props)}"
                )
            else:
                click.echo(
                    "\nWARNING: None of the standard properties appear to be changeable with OpenCV."
                )
                click.echo("This may be due to camera driver limitations on macOS.")
                click.echo(
                    "Try using alternative property IDs directly with set-property."
                )
        else:
            click.echo("Failed to open camera")
    finally:
        camera.close()


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option("--name", help="Property name (e.g., GAIN, EXPOSURE)")
@click.option("--value", required=True, type=float, help="Property value to set")
@click.option("--prop-id", type=int, help="Direct property ID (overrides name lookup)")
def set_property(camera_index, name, value, prop_id):
    """Set a specific camera property"""
    # Validate that either name or prop_id is provided
    if name is None and prop_id is None:
        click.echo("Error: Either --name or --prop-id must be provided")
        return

    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            if prop_id is not None:
                # If direct property ID is provided, use it
                click.echo(f"Setting property ID {prop_id} to {value}")
                initial = camera.cap.get(prop_id)
                click.echo(f"Initial value: {initial}")
                result = camera.cap.set(prop_id, value)
                new_value = camera.cap.get(prop_id)
                click.echo(f"After set attempt - value: {new_value}")
                if result and abs(new_value - initial) > 0.01:
                    click.echo(f"Successfully set property ID {prop_id} to {new_value}")
                else:
                    click.echo(
                        f"Failed to change property ID {prop_id} (no change detected)"
                    )
            else:
                # Otherwise use the name-based approach
                result = camera.set_camera_property(name, value)
                if result:
                    click.echo(f"Successfully set {name} to {value}")
                else:
                    click.echo(
                        f"Failed to set {name}. Try using --prop-id with a direct property ID."
                    )
                    click.echo(
                        "Use get-properties to see what properties are changeable."
                    )
        else:
            click.echo("Failed to open camera")
    finally:
        camera.close()


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option("--gain", required=True, type=int, help="Gain value (typically 0-100)")
def set_gain(camera_index, gain):
    """Set camera gain value"""
    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            result = camera.set_gain(gain)
            if result:
                click.echo(f"Successfully set gain to {gain}")
            else:
                click.echo(f"Failed to set gain to {gain}")
                click.echo("macOS camera drivers often have limited control over gain.")
                click.echo("Try these alternative approaches:")
                click.echo(
                    "1. Try setting a direct property ID: elp-camera set-property --camera-index 1 --prop-id 81 --value 70"
                )
                click.echo(
                    "2. Check which properties are changeable: elp-camera get-properties --camera-index 1"
                )
        else:
            click.echo("Failed to open camera")
    finally:
        camera.close()


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option(
    "--exposure", required=True, type=int, help="Exposure value (negative for auto)"
)
def set_exposure(camera_index, exposure):
    """Set camera exposure value"""
    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            result = camera.set_exposure(exposure)
            if result:
                click.echo(f"Successfully set exposure to {exposure}")
            else:
                click.echo(f"Failed to set exposure to {exposure}")
        else:
            click.echo("Failed to open camera")
    finally:
        camera.close()


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option(
    "--brightness", required=True, type=int, help="Brightness value (typically 0-100)"
)
def set_brightness(camera_index, brightness):
    """Set camera brightness value"""
    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            result = camera.set_brightness(brightness)
            if result:
                click.echo(f"Successfully set brightness to {brightness}")
            else:
                click.echo(f"Failed to set brightness to {brightness}")
        else:
            click.echo("Failed to open camera")
    finally:
        camera.close()


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option("--auto/--manual", required=True, help="Enable or disable auto exposure")
def set_auto_exposure(camera_index, auto):
    """Enable or disable auto exposure"""
    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            # Convert bool to int (0=manual, 1=auto)
            auto_val = 1 if auto else 0
            result = camera.set_auto_exposure(auto_val)
            if result:
                click.echo(
                    f"Successfully set auto exposure to {'ON' if auto else 'OFF'}"
                )
            else:
                click.echo(f"Failed to set auto exposure to {'ON' if auto else 'OFF'}")
        else:
            click.echo("Failed to open camera")
    finally:
        camera.close()


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option("--min-id", type=int, default=0, help="Minimum property ID to scan")
@click.option("--max-id", type=int, default=100, help="Maximum property ID to scan")
@click.option(
    "--test-value", type=float, default=50, help="Value to test setting properties to"
)
@click.option(
    "--focus-id",
    type=int,
    help="Focus on testing a specific property ID with multiple values",
)
def scan_properties(camera_index, min_id, max_id, test_value, focus_id):
    """Scan a range of property IDs to find which ones work with your camera"""
    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            if focus_id is not None:
                # Focus on testing a single property ID with multiple values
                click.echo(f"Testing property ID {focus_id} with multiple values...")
                test_property_with_values(camera, focus_id)
            else:
                # Scan a range of property IDs
                click.echo(f"Scanning property IDs from {min_id} to {max_id}...")
                click.echo("This may take a while. Press Ctrl+C to interrupt.")

                working_props = []
                nonzero_props = []

                # First, take initial frames to stabilize the camera
                for _ in range(3):
                    ret, _ = camera.cap.read()

                for prop_id in range(min_id, max_id + 1):
                    try:
                        # Get initial value
                        initial_value = camera.cap.get(prop_id)

                        # If property has a non-zero value, note it
                        if abs(initial_value) > 0.01:
                            nonzero_props.append((prop_id, initial_value))

                        # Try to set different values
                        changes_detected = []

                        # Test various differences from initial value
                        test_changes = [20, -20, 50, -50, 100, -100]
                        if (
                            prop_id == 4
                        ):  # Special handling for property 4 which seems to work
                            # Property 4 might be height related, test more values
                            test_changes = [100, 200, 300, 400, 500, 600, 700, 800]

                        for change in test_changes:
                            try:
                                # Skip negative values
                                test_val = initial_value + change
                                if test_val <= 0:
                                    continue

                                # Take a frame to stabilize the camera
                                ret, _ = camera.cap.read()

                                # Try setting the property
                                result = camera.cap.set(prop_id, test_val)

                                # Take another frame to apply changes
                                ret, _ = camera.cap.read()

                                # Check new value
                                new_value = camera.cap.get(prop_id)

                                if result and abs(new_value - initial_value) > 0.1:
                                    changes_detected.append((test_val, new_value))
                                    click.echo(
                                        f"✅ Property ID {prop_id}: Changed from {initial_value} to {new_value} by setting to {test_val}"
                                    )

                                    # Reset to original value
                                    camera.cap.set(prop_id, initial_value)
                                    ret, _ = camera.cap.read()

                                    # We've found at least one value that works, so we can move on
                                    break
                            except Exception as e:
                                click.echo(
                                    f"Error testing prop {prop_id} with change {change}: {str(e)}"
                                )
                                continue

                        if changes_detected:
                            working_props.append(
                                (prop_id, initial_value, changes_detected)
                            )

                    except Exception as e:
                        click.echo(f"Error testing property ID {prop_id}: {str(e)}")
                        continue

                    # Simple progress indicator
                    if (prop_id - min_id) % 10 == 0:
                        click.echo(f"Scanning... currently at ID {prop_id}")

                # Report results
                click.echo("\n--- SCAN RESULTS ---")

                if working_props:
                    click.echo("\nProperties that can be changed:")
                    for prop_id, initial, changes in working_props:
                        click.echo(
                            f"Property ID {prop_id}: Initial={initial}, Working values:"
                        )
                        for target, actual in changes:
                            click.echo(f"  - Set to {target} → got {actual}")

                    # Special instructions for property ID 4 which seems to work
                    if any(p[0] == 4 for p in working_props):
                        click.echo(
                            "\nSPECIAL NOTE: Property ID 4 can be adjusted. Try these commands:"
                        )
                        click.echo(
                            "elp-camera set-property --camera-index 1 --prop-id 4 --value 1100"
                        )
                        click.echo(
                            "elp-camera set-property --camera-index 1 --prop-id 4 --value 1200"
                        )
                        click.echo(
                            "elp-camera set-property --camera-index 1 --prop-id 4 --value 1300"
                        )

                    click.echo(
                        "\nUse these properties with: elp-camera set-property --camera-index 1 --prop-id ID --value VALUE"
                    )
                else:
                    click.echo("No changeable properties found in this range.")

                if nonzero_props:
                    click.echo(
                        "\nProperties with non-zero values (but couldn't be changed):"
                    )
                    for prop_id, value in nonzero_props:
                        if not any(p[0] == prop_id for p in working_props):
                            click.echo(f"Property ID {prop_id}: {value}")

                click.echo("\nScan complete!")
        else:
            click.echo("Failed to open camera")
    except KeyboardInterrupt:
        click.echo("\nScan interrupted.")
    finally:
        camera.close()


def test_property_with_values(camera, prop_id):
    """Test a specific property ID with multiple values"""
    # Get initial value
    initial_value = camera.cap.get(prop_id)
    click.echo(f"Property ID {prop_id} initial value: {initial_value}")

    # Get a test frame and initial dimensions
    ret, frame = camera.cap.read()
    initial_width, initial_height = None, None
    if ret and frame is not None:
        initial_width, initial_height = frame.shape[1], frame.shape[0]
        click.echo(f"Current frame resolution: {initial_width}x{initial_height}")

    # Try a much wider range of values with larger steps
    click.echo("Testing values with different scales...")

    working_values = []

    # Test powers of 2 (which often matter in video settings)
    test_vals = [
        # Try powers of 2 which are common in video settings
        16,
        32,
        64,
        128,
        256,
        512,
        1024,
        2048,
        4096,
        8192,
        # Also try standard video heights
        240,
        480,
        720,
        1080,
        1440,
        2160,
        # Try multiples of initial value
        int(initial_value * 0.25),
        int(initial_value * 0.5),
        int(initial_value * 1.5),
        int(initial_value * 2),
        int(initial_value * 4),
        int(initial_value * 8),
        # Try very different values to see if any cause a change
        1,
        100,
        1000,
        10000,
    ]

    # Remove duplicates and sort
    test_vals = sorted(list(set([v for v in test_vals if v > 0])))

    # Test each value
    for test_val in test_vals:
        # Skip if too close to initial value
        if abs(test_val - initial_value) < 10:
            continue

        click.echo(f"  Testing value: {test_val}")
        try:
            # Take a frame first
            ret, _ = camera.cap.read()

            # Try setting the property
            result = camera.cap.set(prop_id, test_val)

            # Take a few frames to let the change apply
            for _ in range(3):
                ret, frame = camera.cap.read()

            # Get the new value and frame properties
            new_value = camera.cap.get(prop_id)

            # Check if value changed
            if abs(new_value - initial_value) > 0.1:
                click.echo(f"  ✅ Value changed to: {new_value}")
                if ret and frame is not None:
                    click.echo(f"  New resolution: {frame.shape[1]}x{frame.shape[0]}")
                working_values.append(
                    (
                        test_val,
                        new_value,
                        frame.shape if ret and frame is not None else None,
                    )
                )
            else:
                click.echo(f"  ❌ No value change: {new_value}")
                if (
                    ret
                    and frame is not None
                    and initial_width is not None
                    and initial_height is not None
                ):
                    # Still check if frame dimensions changed even if property didn't
                    if (
                        frame.shape[0] != initial_height
                        or frame.shape[1] != initial_width
                    ):
                        click.echo(
                            f"  ⚠️ But resolution changed to: {frame.shape[1]}x{frame.shape[0]}"
                        )
                        working_values.append((test_val, new_value, frame.shape))
        except Exception as e:
            click.echo(f"  Error testing value {test_val}: {str(e)}")

        # Reset to initial value between tests
        camera.cap.set(prop_id, initial_value)
        for _ in range(2):  # Multiple frames to ensure it takes effect
            ret, _ = camera.cap.read()

    # Report results
    if working_values:
        click.echo(f"\nWorking values for property ID {prop_id}:")
        for val, actual, shape in working_values:
            shape_info = (
                f", Resolution: {shape[1]}x{shape[0]}" if shape is not None else ""
            )
            click.echo(f"Set to {val} → got {actual}{shape_info}")
    else:
        click.echo(f"\nNo working values found for property ID {prop_id}")

    # Try different property setting strategy - change resolution first, then property
    click.echo("\nTrying with resolution changes:")

    # Define some resolution index pairs to try
    resolution_pairs = [
        (17, 640, 480),  # Low resolution
        (11, 1920, 1080),  # Medium resolution
        (1, 4656, 3496),  # High resolution
    ]

    for res_idx, width, height in resolution_pairs:
        click.echo(f"\nSwitching to resolution index {res_idx} ({width}x{height}):")

        # Try setting the resolution
        try:
            # Close and reopen with new resolution
            camera.close()
            if camera.open(resolution_index=res_idx, force_camera_index=True):
                # Verify current resolution
                ret, frame = camera.cap.read()
                if ret and frame is not None:
                    current_width, current_height = frame.shape[1], frame.shape[0]
                    current_value = camera.cap.get(prop_id)
                    click.echo(
                        f"  Resolution: {current_width}x{current_height}, Property {prop_id}: {current_value}"
                    )

                    # Try setting the property at this resolution
                    for test_val in [
                        current_value + 100,
                        current_value + 500,
                        current_value * 2,
                    ]:
                        if test_val <= 0:
                            continue

                        click.echo(f"  Testing value: {test_val}")
                        camera.cap.set(prop_id, test_val)

                        # Take a few frames to let change apply
                        for _ in range(3):
                            ret, frame = camera.cap.read()

                        # Check if it had an effect
                        new_value = camera.cap.get(prop_id)
                        if ret and frame is not None:
                            click.echo(
                                f"  Value: {new_value}, Resolution: {frame.shape[1]}x{frame.shape[0]}"
                            )

                            if (
                                abs(new_value - current_value) > 0.1
                                or frame.shape[0] != current_height
                                or frame.shape[1] != current_width
                            ):
                                click.echo("  ✅ Change detected!")
                                working_values.append(
                                    (test_val, new_value, frame.shape if ret else None)
                                )
            else:
                click.echo("  Failed to open camera with this resolution")
        except Exception as e:
            click.echo(f"  Error with resolution {res_idx}: {str(e)}")

    # Report final results
    if working_values:
        click.echo(f"\nAll working combinations for property ID {prop_id}:")
        for val, actual, shape in working_values:
            shape_info = (
                f", Resolution: {shape[1]}x{shape[0]}" if shape is not None else ""
            )
            click.echo(f"Set to {val} → got {actual}{shape_info}")
    else:
        click.echo(
            f"\nNo working values found for property ID {prop_id} in any configuration"
        )

    # Reset to original resolution and value
    camera.close()
    camera.open(force_camera_index=True)


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option(
    "--height",
    type=int,
    required=True,
    help="Height value to set (e.g., 1200, 1300, 1744)",
)
def set_height(camera_index, height):
    """Set camera's vertical resolution height (works on macOS with ELP cameras)"""
    # Property ID 4 controls vertical resolution on ELP cameras
    PROP_ID = 4

    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            # Get current resolution info
            ret, frame = camera.cap.read()
            if ret:
                current_width = frame.shape[1]
                current_height = frame.shape[0]
                click.echo(f"Current resolution: {current_width}x{current_height}")

            # Get current property value
            initial_height = camera.cap.get(PROP_ID)
            click.echo(f"Current height property value: {initial_height}")

            if height <= 0:
                click.echo("Height must be greater than 0")
                return

            # Set the new height
            click.echo(f"Setting height to {height}...")
            result = camera.cap.set(PROP_ID, height)

            # Take a frame to apply changes
            ret, frame = camera.cap.read()

            # Check if it worked
            new_height = camera.cap.get(PROP_ID)
            if ret and frame is not None:
                actual_width = frame.shape[1]
                actual_height = frame.shape[0]
                click.echo(f"New resolution: {actual_width}x{actual_height}")

            if result and abs(new_height - initial_height) > 0.1:
                click.echo(
                    f"✅ Successfully changed height property from {initial_height} to {new_height}"
                )

                # Try a few more frames to see if resolution stabilizes
                for i in range(5):
                    ret, frame = camera.cap.read()
                    if ret and frame is not None:
                        click.echo(
                            f"Frame {i + 1} resolution: {frame.shape[1]}x{frame.shape[0]}"
                        )
            else:
                click.echo("❌ Failed to change height (no change detected)")
                click.echo("This may be because:")
                click.echo("- The requested height is less than the current value")
                click.echo("- The camera doesn't support this height value")
                click.echo("- The macOS camera driver is restricting property changes")
                click.echo(
                    "\nTry using --height with a value higher than the current value"
                )
        else:
            click.echo("Failed to open camera")
    finally:
        camera.close()


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option("--min-id", type=int, default=0, help="Minimum property ID to scan")
@click.option("--max-id", type=int, default=600, help="Maximum property ID to scan")
@click.option(
    "--skip",
    type=int,
    default=1,
    help="Skip factor for IDs (higher values scan faster but may miss properties)",
)
def deep_scan_properties(camera_index, min_id, max_id, skip):
    """Deep scan of property IDs with frame capture to find any that affect the camera"""
    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            click.echo(
                f"Deep scanning property IDs from {min_id} to {max_id} (skip={skip})..."
            )
            click.echo("This may take a while. Press Ctrl+C to interrupt.")

            # Get baseline frame
            ret, base_frame = camera.cap.read()
            if not ret or base_frame is None:
                click.echo("Failed to get baseline frame")
                return

            base_width, base_height = base_frame.shape[1], base_frame.shape[0]
            click.echo(f"Baseline resolution: {base_width}x{base_height}")

            # Track properties with visible effects
            working_props = []
            nonzero_props = []
            resolution_changing_props = []

            # Progress tracking
            total_ids = (max_id - min_id + 1) // skip
            ids_checked = 0
            last_percent = 0

            # Test values to try for each property
            test_values = [1, 10, 100, 500, 1000, 2000, 4000, 8000]

            # Scan each property ID
            for prop_id in range(min_id, max_id + 1, skip):
                try:
                    # Update progress
                    ids_checked += 1
                    percent_done = (ids_checked * 100) // total_ids
                    if percent_done > last_percent and percent_done % 5 == 0:
                        last_percent = percent_done
                        click.echo(f"Progress: {percent_done}% complete")

                    # Get initial value
                    initial_value = camera.cap.get(prop_id)
                    if abs(initial_value) > 0.01:
                        nonzero_props.append((prop_id, initial_value))
                        click.echo(
                            f"Property {prop_id} has non-zero value: {initial_value}"
                        )

                    # Try different values and check for changes in:
                    # 1. Returned property value
                    # 2. Frame resolution
                    # 3. Frame appearance (would need image comparison)
                    prop_affects_camera = False

                    # Only test a few values to save time
                    for test_val in test_values:
                        if test_val == initial_value:
                            continue

                        # Take a frame to stabilize
                        ret, _ = camera.cap.read()

                        # Try setting the property
                        try:
                            result = camera.cap.set(prop_id, test_val)
                        except Exception:
                            # Skip if property throws an error
                            break

                        # Take a few frames to apply changes
                        frames = []
                        for _ in range(3):
                            ret, frame = camera.cap.read()
                            if ret and frame is not None:
                                frames.append(frame)

                        if not frames:
                            # If we can't get frames after setting property, this might
                            # be a problematic property - reset camera and skip
                            click.echo(
                                f"⚠️ Warning: Property {prop_id} causes frame capture issues"
                            )
                            camera.close()
                            camera.open(force_camera_index=True)
                            break

                        # Check the new value
                        new_value = camera.cap.get(prop_id)

                        # Check if property value changed
                        if abs(new_value - initial_value) > 0.1:
                            click.echo(
                                f"✅ Property {prop_id}: Value changed from {initial_value} to {new_value}"
                            )
                            working_props.append(
                                (prop_id, initial_value, new_value, test_val)
                            )
                            prop_affects_camera = True
                            break

                        # Check if resolution changed
                        last_frame = frames[-1]
                        if (
                            last_frame.shape[1] != base_width
                            or last_frame.shape[0] != base_height
                        ):
                            new_width, new_height = (
                                last_frame.shape[1],
                                last_frame.shape[0],
                            )
                            click.echo(
                                f"✅ Property {prop_id}: Changed resolution from {base_width}x{base_height} to {new_width}x{new_height}"
                            )
                            resolution_changing_props.append(
                                (
                                    prop_id,
                                    f"{base_width}x{base_height}",
                                    f"{new_width}x{new_height}",
                                    test_val,
                                )
                            )
                            prop_affects_camera = True
                            break

                        # Reset property to original value
                        camera.cap.set(prop_id, initial_value)
                        ret, _ = camera.cap.read()

                    # If this property affects the camera, make sure we reset properly
                    if prop_affects_camera:
                        # Take extra steps to ensure camera is back to normal
                        camera.cap.set(prop_id, initial_value)
                        for _ in range(3):
                            ret, _ = camera.cap.read()

                except Exception as e:
                    click.echo(f"Error testing property {prop_id}: {str(e)}")
                    # Try to recover
                    try:
                        camera.close()
                        camera.open(force_camera_index=True)
                    except:
                        click.echo("Failed to recover camera, exiting")
                        return

            # Report results
            click.echo("\n--- DEEP SCAN RESULTS ---")

            if working_props:
                click.echo("\nProperties that can be changed (value changed):")
                for prop_id, initial, new_val, set_val in working_props:
                    click.echo(
                        f"Property ID {prop_id}: Initial={initial}, Changed to {new_val} by setting to {set_val}"
                    )

            if resolution_changing_props:
                click.echo("\nProperties that change resolution:")
                for prop_id, old_res, new_res, set_val in resolution_changing_props:
                    click.echo(
                        f"Property ID {prop_id}: Changed resolution from {old_res} to {new_res} by setting to {set_val}"
                    )

            if nonzero_props:
                click.echo("\nProperties with non-zero values:")
                for prop_id, value in nonzero_props:
                    if not any(p[0] == prop_id for p in working_props):
                        click.echo(f"Property ID {prop_id}: {value}")

            if not working_props and not resolution_changing_props:
                click.echo("No properties found that affect the camera")

            # Provide usage instructions for any found properties
            if working_props or resolution_changing_props:
                all_props = set(
                    [p[0] for p in working_props]
                    + [p[0] for p in resolution_changing_props]
                )
                click.echo("\nUse these properties with:")
                for prop_id in all_props:
                    click.echo(
                        f"elp-camera set-property --camera-index 1 --prop-id {prop_id} --value VALUE"
                    )

            click.echo("\nDeep scan complete!")
        else:
            click.echo("Failed to open camera")
    except KeyboardInterrupt:
        click.echo("\nScan interrupted.")
    finally:
        # Make sure to close the camera
        camera.close()


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option("--width", type=int, required=True, help="Width to set")
@click.option("--height", type=int, required=True, help="Height to set")
@click.option(
    "--force", is_flag=True, help="Force resolution by trying multiple methods"
)
def set_resolution(camera_index, width, height, force):
    """Attempt to set camera resolution using multiple methods"""
    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            # Get current resolution
            ret, frame = camera.cap.read()
            if ret and frame is not None:
                current_width, current_height = frame.shape[1], frame.shape[0]
                click.echo(f"Current resolution: {current_width}x{current_height}")
            else:
                click.echo("Failed to get current resolution")
                return

            # First try the standard approach
            click.echo(
                f"Trying to set resolution to {width}x{height} (Standard method)..."
            )

            # Get current property values
            cv_width = camera.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            cv_height = camera.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

            click.echo(f"Current property values: Width={cv_width}, Height={cv_height}")

            # Try setting resolution directly
            camera.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            camera.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            # Take a few frames to allow changes to apply
            for _ in range(5):
                ret, frame = camera.cap.read()

            # Check if it worked
            if ret and frame is not None:
                new_width, new_height = frame.shape[1], frame.shape[0]
                click.echo(f"New resolution: {new_width}x{new_height}")

                if new_width == width and new_height == height:
                    click.echo("✅ Successfully set resolution using standard method")
                else:
                    click.echo("❌ Failed to set resolution using standard method")
            else:
                click.echo("Failed to get frame after setting resolution")

            # If standard method didn't work and force is enabled, try alternative approaches
            if force and (new_width != width or new_height != height):
                click.echo("\nTrying alternative methods...")

                # Try Method 2: Close and reopen with resolution
                click.echo("Method 2: Close and reopen with resolution...")
                camera.close()
                camera.cap = cv2.VideoCapture(camera_index)

                if camera.cap.isOpened():
                    # Set properties in specific order
                    camera.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    camera.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

                    # Take some frames
                    for _ in range(5):
                        ret, frame = camera.cap.read()

                    # Check result
                    if ret and frame is not None:
                        new_width, new_height = frame.shape[1], frame.shape[0]
                        click.echo(f"Method 2 result: {new_width}x{new_height}")

                        if new_width == width and new_height == height:
                            click.echo("✅ Method 2 successful")
                        else:
                            click.echo("❌ Method 2 failed")
                    else:
                        click.echo("Method 2 failed to get frame")

                # Try Method 3: Set format and then resolution
                click.echo("\nMethod 3: Set format first...")
                camera.close()
                camera.cap = cv2.VideoCapture(camera_index)

                if camera.cap.isOpened():
                    # Try both MJPEG and YUY2 formats
                    formats = [
                        ("MJPEG", cv2.VideoWriter_fourcc(*"MJPG")),
                        ("YUY2", cv2.VideoWriter_fourcc(*"YUY2")),
                    ]

                    for fmt_name, fourcc in formats:
                        click.echo(f"Trying format: {fmt_name}")

                        # Set format first, then resolution
                        camera.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
                        camera.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        camera.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

                        # Take some frames
                        frames = []
                        for _ in range(5):
                            ret, frame = camera.cap.read()
                            if ret and frame is not None:
                                frames.append(frame)

                        if frames:
                            last_frame = frames[-1]
                            new_width, new_height = (
                                last_frame.shape[1],
                                last_frame.shape[0],
                            )
                            click.echo(
                                f"Result with {fmt_name}: {new_width}x{new_height}"
                            )

                            if new_width == width and new_height == height:
                                click.echo(
                                    f"✅ Successfully set resolution with {fmt_name} format"
                                )
                                break

                # Try Method 4: Indirect property settings
                click.echo("\nMethod 4: Trying property ID 4 to affect resolution...")
                camera.close()
                camera.cap = cv2.VideoCapture(camera_index)

                if camera.cap.isOpened():
                    ret, frame = camera.cap.read()
                    if ret and frame is not None:
                        # Get initial property value
                        prop4_value = camera.cap.get(4)
                        click.echo(f"Property ID 4 current value: {prop4_value}")

                        # Try different values based on desired height
                        test_values = [height, height * 1.2, height * 1.5, height * 2]

                        for test_val in test_values:
                            click.echo(f"Setting property ID 4 to {test_val}...")
                            camera.cap.set(4, test_val)

                            # Take frames to apply
                            for _ in range(5):
                                ret, frame = camera.cap.read()

                            if ret and frame is not None:
                                new_width, new_height = frame.shape[1], frame.shape[0]
                                click.echo(
                                    f"Resolution after setting to {test_val}: {new_width}x{new_height}"
                                )

                                # Check if we're closer to target
                                if abs(new_height - height) < abs(
                                    current_height - height
                                ):
                                    click.echo("✅ Made progress toward target height")

                # Provide summary
                click.echo("\nResolution setting summary:")
                click.echo(f"Target: {width}x{height}")
                click.echo(f"Best achieved: {new_width}x{new_height}")

                if new_width == width and new_height == height:
                    click.echo("✅ Successfully set exact resolution")
                else:
                    click.echo("⚠️ Could not set exact resolution")
                    click.echo(
                        "Try a different resolution or use one of the predefined resolution indices"
                    )

                    # Suggest closest preset resolution
                    click.echo("\nClosest preset resolutions:")
                    for i, res in enumerate(camera.RESOLUTIONS):
                        if (
                            abs(res["width"] - width) < 300
                            and abs(res["height"] - height) < 300
                        ):
                            click.echo(
                                f"Resolution index {i}: {res['width']}x{res['height']} ({res['format']})"
                            )

                    click.echo(
                        "\nUse with: elp-camera preview --camera-index 1 --resolution-index INDEX"
                    )
        else:
            click.echo("Failed to open camera")
    finally:
        camera.close()


@cli.command()
@click.option(
    "--camera-index",
    type=int,
    required=True,
    help="Camera index (0=built-in, 1=iPhone/external, 2+=other)",
)
@click.option(
    "--fps", required=True, type=float, help="FPS value to set (e.g., 5, 10, 15, 30)"
)
def set_fps(camera_index, fps):
    """Set camera FPS (frames per second) value"""
    if fps <= 0:
        click.echo("FPS value must be greater than 0")
        return

    camera = ELPUVCCamera(camera_index)
    try:
        if camera.open(force_camera_index=True):
            # Use the dedicated method to set FPS
            result = camera.set_fps(fps)

            if result:
                click.echo(f"✅ Successfully changed FPS to {fps}")

                # Test camera with new FPS
                click.echo("Testing camera with new FPS setting...")
                start_time = time.time()
                frames_captured = 0
                test_duration = 3  # Test for 3 seconds

                while time.time() - start_time < test_duration:
                    ret, frame = camera.cap.read()
                    if ret:
                        frames_captured += 1
                    time.sleep(0.01)  # Small sleep to prevent CPU hogging

                actual_fps = frames_captured / test_duration
                click.echo(f"Actual measured FPS: {actual_fps:.2f}")

                if abs(actual_fps - fps) > 5:
                    click.echo(
                        f"⚠️ Note: Actual FPS ({actual_fps:.2f}) differs from requested FPS ({fps})"
                    )
                    click.echo(
                        "This is common with USB cameras where the driver may limit available FPS values"
                    )

                # Provide suggestions for optimal FPS values
                if actual_fps < 10 and fps > 15:
                    click.echo("\nSuggestions for improved performance:")
                    click.echo("- Try a lower resolution for higher frame rates")
                    click.echo(
                        "- Use resolution index 11 (1920x1080) or 17 (640x480) for better FPS"
                    )
                    click.echo(
                        "- Some USB cameras have bandwidth limitations that restrict FPS at higher resolutions"
                    )
            else:
                click.echo("❌ Failed to change FPS")
                click.echo("This may be because:")
                click.echo("- The camera doesn't support changing FPS")
                click.echo("- The requested FPS value is not supported")
                click.echo("- The macOS camera driver is restricting property changes")
                click.echo(
                    "\nTry using a different FPS value or restart the camera first"
                )
        else:
            click.echo("Failed to open camera")
    finally:
        camera.close()


if __name__ == "__main__":
    cli()
