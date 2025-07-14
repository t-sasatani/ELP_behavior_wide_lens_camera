import cv2

CAMERA_INDEX = 1  # Change if needed
RESOLUTIONS = [
    (1920, 1080),
    (1280, 960),
    (1024, 768),
    (800, 600),
    (640, 480),
]
FPS_VALUES = [30, 20, 10]

for width, height in RESOLUTIONS:
    for fps in FPS_VALUES:
        print(f"\nTesting resolution: {width}x{height} at {fps} FPS")
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_AVFOUNDATION)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        success_count = 0
        for i in range(10):
            ret, frame = cap.read()
            if ret:
                print(f"  Frame {i + 1} OK")
                success_count += 1
            else:
                print(f"  Frame {i + 1} FAILED")
        cap.release()
        if success_count == 10:
            print(f"  SUCCESS: {width}x{height} at {fps} FPS works!")
        else:
            print(f"  FAILED: {width}x{height} at {fps} FPS did not work reliably.")
