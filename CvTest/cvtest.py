import os
import cv2
import time
from collections import deque
from datetime import datetime
from google.cloud import storage
from gpiozero import Button
import numpy as np

# Configuration
STATE = "mg"
CITY = "belohorizonte"
COURT = "duna"
RTSP_URL = "rtsp://apertaiCam1:130355va@10.0.0.133/stream1"
BUCKET_NAME = "videos-283812"
CREDENTIALS_PATH = "/home/abidu/Desktop/keys.json"
FRAME_RATE = 30  # Assuming 30 FPS
BUFFER_SIZE = FRAME_RATE * 30  # 30 seconds of video

# Circular buffer to store frames
frame_buffer = deque(maxlen=BUFFER_SIZE)

def capture_video():
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        print("Error opening video stream")
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Add frame to buffer
        frame_buffer.append(frame)

        time.sleep(1 / FRAME_RATE)

def save_last_30_seconds():
    datetime_now = datetime.now()
    datetime_now_formatted = f"{datetime_now.day:02}{datetime_now.month:02}{datetime_now.year}-{datetime_now.hour:02}{datetime_now.minute:02}{datetime_now.second:02}"
    output_file_name = f"{STATE}-{CITY}-{COURT}-{datetime_now_formatted}.mp4"

    # Get the width and height of the frames
    height, width, _ = frame_buffer[0].shape

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file_name, fourcc, FRAME_RATE, (width, height))

    for frame in frame_buffer:
        out.write(frame)

    out.release()
    print(f"Saved last 30 seconds: {output_file_name}")
    return output_file_name

def upload_to_google_cloud(file_name):
    client = storage.Client.from_service_account_json(CREDENTIALS_PATH)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(os.path.basename(file_name).replace("-", "/"))
    blob.upload_from_filename(file_name, content_type='application/octet-stream')
    print(f"Uploaded {file_name} to {BUCKET_NAME}")
    os.remove(file_name)  # Clean up the local file

def on_press(key):
    try:
        if key.char == '1':
            print("Saving last 30 seconds of video...")
            final_video = save_last_30_seconds()
            upload_to_google_cloud(final_video)
    except AttributeError:
        pass

def main():
    print("Starting continuous capture for RTSP stream...")

    # Start capturing video in a separate thread
    import threading
    capture_thread = threading.Thread(target=capture_video)
    capture_thread.start()

    # Set up button press on GPIO port 16
    button = Button(16)

    while True:
        if not button.is_pressed:
            print("Button pressed! Saving last 30 seconds of video...")
            final_video = save_last_30_seconds()
            upload_to_google_cloud(final_video)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
