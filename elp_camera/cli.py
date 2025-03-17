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
def preview(resolution_index, camera_index, config):
    """Preview camera feed"""
    if config and os.path.exists(config):
        camera_config = CameraConfig.from_yaml(config)
        resolution_index = getattr(camera_config, "resolution_index", resolution_index)
        if camera_index is None and hasattr(camera_config, "camera_id"):
            camera_index = getattr(camera_config, "camera_id")

    camera = ELPUVCCamera(camera_index)
    try:
        force_camera = camera_index is not None
        if camera.open(resolution_index, force_camera_index=force_camera):
            camera.preview()
        else:
            click.echo(
                "Failed to open camera. Try specifying --camera-index explicitly."
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
def record(resolution_index, camera_index, output_dir, config):
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
        if camera.open(
            resolution_index, force_camera_index=force_camera, recording_mode=True
        ):
            camera.record(output_dir)
        else:
            click.echo(
                "Failed to open camera. Try specifying --camera-index 1 and --resolution-index 11."
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


if __name__ == "__main__":
    cli()
