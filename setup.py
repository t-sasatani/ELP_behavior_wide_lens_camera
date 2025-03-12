from setuptools import setup, find_packages

setup(
    name="ELP_behavior_wide_lens_camera",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "click",
        "numpy",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "elp-camera=elp_camera.cli:cli",
        ],
    },
)
