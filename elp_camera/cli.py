import click
import os
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


if __name__ == "__main__":
    cli()
