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
BUCKET_NAME = "apertai-cloud"
CREDENTIALS_PATH = "C:/Users/Abidu/ApertAI/key.json"

cameras = {
    "cam1": "rtsp://apertaiCam1:130355va@192.168.0.23/stream1",
    "cam2": "rtsp://apertaiCam2:130355va@192.168.0.25/stream1",
    "cam3": "rtsp://apertaiCam3:130355va@192.168.0.26/stream1"
}

buttons = {
    "button1": Button(25),
    "button2": Button(24),
    "button3": Button(23)
}

def start_buffer_stream(cam_id, rtsp_url):
    print(f"Starting buffer for {cam_id} at {datetime.now()}")
    
    buffer_command = [
        'ffmpeg',
        '-i', rtsp_url,
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',
        '-segment_wrap', '1',
        '-reset_timestamps', '1',
        f'{cam_id}_buffer-%03d.ts'
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def save_last_30_seconds_from_buffer(cam_id, datetime_start_recording):
    datetime_now = datetime.now()
    datetime_now_formatted = f"{datetime_now.day:02}{datetime_now.month:02}{datetime_now.year}-{datetime_now.hour:02}{datetime_now.minute:02}{datetime_now.second:02}"
    output_file_name = os.path.abspath(f"{STATE}-{CITY}-{COURT}-{cam_id}-{datetime_now_formatted}.mp4")
    
    diff = datetime_now - datetime_start_recording
    seconds_diff = diff.seconds % 60
    
    if seconds_diff < 30:
        buffer_file = f'{cam_id}_buffer-000.ts'
    else:
        buffer_file = f'{cam_id}_buffer-000.ts'
    
    save_command = [
        'ffmpeg',
        '-sseof', '-30',
        '-i', buffer_file,
        '-c', 'copy',
        output_file_name
    ]
    
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

def handle_button_press(cam_id, datetime_start_recording):
    print(f"Button pressed for {cam_id}, saving last 30 seconds...")
    final_video = save_last_30_seconds_from_buffer(cam_id, datetime_start_recording)
    upload_to_google_cloud(final_video)

def main():
    print("Starting continuous buffer for RTSP streams...")
    datetime_start_recording = datetime.now()
    print(f"Started at: {datetime_start_recording}")

    for cam_id, rtsp_url in cameras.items():
        start_buffer_stream(cam_id, rtsp_url)
    
    print("Buffers started. Press the corresponding button to save the last 30 seconds of video.")

    while True:
        for cam_id, button in buttons.items():
            if button.is_pressed:
                handle_button_press(cam_id, datetime_start_recording)
                time.sleep(1)  # Debounce button press

if __name__ == "__main__":
    main()
