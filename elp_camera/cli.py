import click
import cv2
import os
from .camera import ELPCamera
from .recorder import CameraRecorder
from .config import CameraConfig


@click.group()
def cli():
    """ELP Camera Control CLI"""
    pass


@cli.command()
@click.option("--camera-id", default=0, help="Camera device ID")
@click.option("--resolution-index", default=0, help="Resolution index (0-7)")
@click.option("--config", type=str, help="Path to YAML configuration file")
def preview(
    camera_id: int,
    resolution_index: int,
    config: str,
):
    """Preview camera feed"""
    if config and os.path.exists(config):
        camera_config = CameraConfig.from_yaml(config)
    else:
        camera_config = CameraConfig(
            camera_id=camera_id,
            resolution_index=resolution_index,
        )

    camera = ELPCamera(camera_config.camera_id)

    try:
        camera.open()
        if 0 <= camera_config.resolution_index < len(camera.RESOLUTIONS):
            width, height, fps = camera.RESOLUTIONS[camera_config.resolution_index]
            camera.set_resolution(width, height, fps)
            click.echo(f"Set resolution to {width}x{height} @ {fps}fps")

        while True:
            ret, frame = camera.get_frame()
            if ret:
                cv2.imshow("Preview", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                click.echo("Failed to get frame")
                break

    finally:
        camera.close()
        cv2.destroyAllWindows()


@cli.command()
@click.option("--camera-id", default=0, help="Camera device ID")
@click.option("--resolution-index", default=0, help="Resolution index (0-7)")
@click.option("--output-dir", default="recordings", help="Output directory")
@click.option("--config", type=str, help="Path to YAML configuration file")
def record(
    camera_id: int,
    resolution_index: int,
    output_dir: str,
    config: str,
):
    """Record video with Unix timestamp filename"""
    # Load config file if provided
    if config and os.path.exists(config):
        camera_config = CameraConfig.from_yaml(config)
    else:
        camera_config = CameraConfig(
            camera_id=camera_id,
            resolution_index=resolution_index,
            output_dir=output_dir,
        )

    camera = ELPCamera(camera_config.camera_id)

    try:
        camera.open()
        if 0 <= camera_config.resolution_index < len(camera.RESOLUTIONS):
            width, height, fps = camera.RESOLUTIONS[camera_config.resolution_index]
            camera.set_resolution(width, height, fps)
            click.echo(f"Set resolution to {width}x{height} @ {fps}fps")

        recorder = CameraRecorder(camera, camera_config.output_dir)
        recorder.start_recording()
        click.echo(f"Recording to {recorder.current_filename}")

        while True:
            ret, frame = camera.get_frame()
            if ret:
                recorder.record_frame(frame)
                cv2.imshow("Recording", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                click.echo("Failed to get frame")
                break

    finally:
        recorder.stop_recording()
        camera.close()
        cv2.destroyAllWindows()


@cli.command()
def list_cameras():
    """List available cameras"""
    cameras = ELPCamera.list_cameras()
    if cameras:
        click.echo(f"Found cameras at indices: {cameras}")
    else:
        click.echo("No cameras found")


if __name__ == "__main__":
    cli()
