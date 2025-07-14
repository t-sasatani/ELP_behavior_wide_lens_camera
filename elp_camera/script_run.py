#!/usr/bin/env python

import cv2
import time
import sys
import threading
import queue

print("Initializing camera...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    sys.exit(1)

# Optimize camera settings
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Test camera first
ret, frame = cap.read()
if not ret:
    print("Error: Cannot read from camera.")
    cap.release()
    sys.exit(1)

# Setup video writer
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
output_filename = f"recording_{int(time.time())}.avi"
out = cv2.VideoWriter(output_filename, fourcc, 30.0, (640, 480))

# Threading for video writing
frame_queue = queue.Queue(maxsize=60)
writing_active = threading.Event()
writing_active.set()

def video_writer_thread():
    while writing_active.is_set() or not frame_queue.empty():
        try:
            frame = frame_queue.get(timeout=0.1)
            out.write(frame)
            frame_queue.task_done()
        except queue.Empty:
            continue

writer_thread = threading.Thread(target=video_writer_thread)
writer_thread.start()

print(f"Recording to {output_filename} - will auto-stop after 10 seconds")
print("Press ESC to exit early")

# Record for 10 seconds
start_time = time.time()
frame_count = 0

while time.time() - start_time < 10:
    ret, frame = cap.read()
    if ret:
        # Show preview
        cv2.imshow('Camera Preview', frame)
        
        # Add frame to recording queue
        try:
            frame_queue.put_nowait(frame)
            frame_count += 1
        except queue.Full:
            continue
    
    # Check for ESC key to exit early
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC key
        print("ESC pressed - stopping recording")
        break

# Cleanup
writing_active.clear()
writer_thread.join()
cap.release()
out.release()
cv2.destroyAllWindows()

elapsed_time = time.time() - start_time
fps = frame_count / elapsed_time
print(f"Recorded {frame_count} frames in {elapsed_time:.1f}s = {fps:.1f} FPS")
print(f"Video saved: {output_filename}")