import subprocess
import os
import time
from datetime import datetime
from google.cloud import storage
from gpiozero import Button

# Configuration
STATE = "mg"
CITY = "belohorizonte"
COURT = "duna"
RTSP_URL = "rtsp://apertaiCam2:130355va@192.168.0.7:554/Streaming/Channels/101"
BUCKET_NAME = "videos-283812"
CREDENTIALS_PATH = "/home/apertai/Desktop/apertaiKeys.json"

def start_buffer_stream_1():
    print(f"Starting cam2 buffer 1 at {datetime.now()}")
    
    # Command for continuous buffer that overwrites itself every 30 seconds
    buffer_command = [
        'ffmpeg',
        '-i', RTSP_URL,
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',  # Duration of each segment
        '-segment_wrap', '1',  # Number of segments to wrap around
        '-reset_timestamps', '1',  # Reset timestamps at the start of each segment
        'cam-2-buffer-1-%03d.ts-%03d.ts'  # Save segments with a numbering pattern
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_buffer_stream_2():
    print(f"Starting cam2 buffer 2 at {datetime.now()}")
    
    # Command for continuous buffer that overwrites itself every 30 seconds
    buffer_command = [
        'ffmpeg',
        '-i', RTSP_URL,
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',  # Duration of each segment
        '-segment_wrap', '1',  # Number of segments to wrap around
        '-reset_timestamps', '1',  # Reset timestamps at the start of each segment
        'cam-2-buffer-2-%03d.ts-%03d.ts'  # Save segments with a numbering pattern
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def save_last_30_seconds_from_buffer(datetime_start_recording):
    datetime_now = datetime.now()
    datetime_now_formatted = f"{datetime_now.day:02}{datetime_now.month:02}{datetime_now.year}-{datetime_now.hour:02}{datetime_now.minute:02}{datetime_now.second:02}"
    output_file_name = os.path.abspath(f"{STATE}-{CITY}-{COURT}-{datetime_now_formatted}.mp4")
    
    print(datetime_now)
    
    diff = datetime_now - datetime_start_recording
    seconds_diff = diff.seconds % 60
    print(diff)
    print(diff.seconds)
    print(seconds_diff)
    
    if seconds_diff < 30:
        # Use buffer 2
        save_command = [
            'ffmpeg',
            '-sseof', '-30',
            '-i', 'cam-2-buffer-2-000.ts',
            '-c', 'copy',
            output_file_name
        ]
        print("Using buffer 2")
    else:
        # Use buffer 1
        save_command = [
            'ffmpeg',
            '-sseof', '-30',
            '-i', 'cam-2-buffer-1-000.ts',
            '-c', 'copy',
            output_file_name
        ]
        print("Using buffer 1")

    subprocess.run(save_command, check=True)
    print(f"Saved last 30 seconds: {output_file_name}")
    return output_file_name

def upload_to_google_cloud(file_name):
    client = storage.Client.from_service_account_json(CREDENTIALS_PATH)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(os.path.basename(file_name).replace("-", "/"))
    blob.upload_from_filename(file_name, content_type='application/octet-stream')
    print(f"Uploaded {file_name} to {BUCKET_NAME}")
    os.remove(file_name)  # Clean up the local file

def main():
    print("Starting continuous buffer for RTSP stream...")
    global datetime_start_recording
    datetime_start_recording = datetime.now()
    print(f"Started at: {datetime.now()}")
    
    start_buffer_stream_1()
    print(f"Sleeping for 30 seconds")
    time.sleep(30)
    print(f"Done sleeping")
    start_buffer_stream_2()
    
    print("Press the button on GPIO port 25 to save the last 30 seconds of video...")

    # Set up button press on GPIO port 24
    button = Button(24)
    
    while True:
        if not button.is_pressed:
            print("Button pressed! Saving last 30 seconds of video...")
            final_video = save_last_30_seconds_from_buffer(datetime_start_recording)
            upload_to_google_cloud(final_video)
        time.sleep(0.1)

if __name__ == "__main__":
    main()