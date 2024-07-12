import subprocess
import os
import time
from datetime import datetime
from google.cloud import storage
from gpiozero import Button
from discover_camera_ip import get_rtsp_ips

# Configuration
STATE = "mg"
CITY = "belohorizonte"
COURT = "duna"
BUCKET_NAME = "videos-283812"
CREDENTIALS_PATH = "/home/apertai/Desktop/apertaiKeys.json"

# Define camera URLs (initially empty, to be filled with discovered IPs)
cameras = {
    "cam1": "rtsp://apertaiCam1:130355va@192.168.0.23/stream1",
    "cam2": "rtsp://apertaiCam2:130355va@192.168.0.25/stream1",
    "cam3": "rtsp://apertaiCam3:130355va@192.168.0.26/stream1"
}

# Setup for recording and buttons
buffers = {}
start_times = {}
buttons = {
    "button1": Button(25),
    "button2": Button(24),
    "button3": Button(23)
}

# Initialize buffer streams for each camera and buffer
def start_buffer_stream_1_1():
    print(f"Starting buffer 1_1 for Camera 1 at {datetime.now()}")
    buffer_command = [
        'ffmpeg',
        '-i', cameras['cam1'],
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',  # Duration of each segment
        '-segment_wrap', '1',  # Number of segments to wrap around
        '-reset_timestamps', '1',  # Reset timestamps at the start of each segment
        'buffer1_1-%03d.ts'  # Save segments with a numbering pattern
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_buffer_stream_1_2():
    print(f"Starting buffer 1_2 for Camera 1 at {datetime.now()}")
    buffer_command = [
        'ffmpeg',
        '-i', cameras['cam1'],
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',
        '-segment_wrap', '1',
        '-reset_timestamps', '1',
        'buffer1_2-%03d.ts'
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_buffer_stream_2_1():
    print(f"Starting buffer 2_1 for Camera 2 at {datetime.now()}")
    buffer_command = [
        'ffmpeg',
        '-i', cameras['cam2'],
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',
        '-segment_wrap', '1',
        '-reset_timestamps', '1',
        'buffer2_1-%03d.ts'
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_buffer_stream_2_2():
    print(f"Starting buffer 2_2 for Camera 2 at {datetime.now()}")
    buffer_command = [
        'ffmpeg',
        '-i', cameras['cam2'],
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',
        '-segment_wrap', '1',
        '-reset_timestamps', '1',
        'buffer2_2-%03d.ts'
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_buffer_stream_3_1():
    print(f"Starting buffer 3_1 for Camera 3 at {datetime.now()}")
    buffer_command = [
        'ffmpeg',
        '-i', cameras['cam3'],
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',
        '-segment_wrap', '1',
        '-reset_timestamps', '1',
        'buffer3_1-%03d.ts'
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_buffer_stream_3_2():
    print(f"Starting buffer 3_2 for Camera 3 at {datetime.now()}")
    buffer_command = [
        'ffmpeg',
        '-i', cameras['cam3'],
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',
        '-segment_wrap', '1',
        '-reset_timestamps', '1',
        'buffer3_2-%03d.ts'
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def save_last_30_seconds_from_buffer(cam_id):
    datetime_now = datetime.now()
    datetime_now_formatted = f"{datetime_now.day:02}{datetime_now.month:02}{datetime_now.year}-{datetime_now.hour:02}{datetime_now.minute:02}{datetime_now.second:02}"
    output_file_name = os.path.abspath(f"{STATE}-{CITY}-{COURT}-{cam_id}-{datetime_now_formatted}.mp4")
    
    buffer_number = 1 if datetime_now.second < 30 else 2
    buffer_file = f'{cam_id}_buffer{buffer_number}-000.ts'
    if not os.path.isfile(buffer_file):
        print(f"No buffer file found for {cam_id}, buffer{buffer_number}")
        return None

    save_command = [
        'ffmpeg',
        '-sseof', '-30',
        '-i', buffer_file,
        '-c', 'copy',
        output_file_name
    ]
    subprocess.run(save_command, check=True)
    print(f"Saved last 30 seconds from {cam_id}: {output_file_name}")
    return output_file_name

def upload_to_google_cloud(file_name):
    client = storage.Client.from_service_account_json(CREDENTIALS_PATH)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(os.path.basename(file_name).replace("-", "/"))
    blob.upload_from_filename(file_name, content_type='application/octet-stream')
    print(f"Uploaded {file_name} to {BUCKET_NAME}")
    os.remove(file_name)

def main():
    # rtsp_devices = get_rtsp_ips()  # Discover the IPs of the RTSP cameras
    # if len(rtsp_devices) < 3:
    #     print("Error: Not all camera IPs were found.")
    #     return

    # Update camera URLs with new IPs
    # for i, ip in enumerate(rtsp_devices):
    #     cameras[f"cam{i+1}"] = f"rtsp://apertaiCam{i+1}:130355va@{ip}/stream1"

    # Start buffer streams for all cameras
    for i in range(1, 4):
        buffers[f'cam{i}'] = [globals()[f'start_buffer_stream_{i}_1'](), globals()[f'start_buffer_stream_{i}_2']()]

    while True:
        time.sleep(1)
        for button_id, button in buttons.items():
            cam_id = button_id.replace("button", "cam")
            if not button.is_pressed:
                final_video = save_last_30_seconds_from_buffer(cam_id)
                upload_to_google_cloud(final_video)

if __name__ == "__main__":
    main()
