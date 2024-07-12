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
    "1": "rtsp://apertaiCam1:130355va@192.168.0.7:554/h264/ch1/main/av_stream",
    "2": "rtsp://apertaiCam2:130355va@192.168.0.8:554/h264/ch1/main/av_stream",
    "3": "rtsp://apertaiCam3:130355va@192.168.0.26:554/h264/ch1/main/av_stream"
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
        '-i', cameras['1'],
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
        '-i', cameras['1'],
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
        '-i', cameras['2'],
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
        '-i', cameras['2'],
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
        '-i', cameras['3'],
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
        '-i', cameras['3'],
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
    buffer_file = f'buffer{cam_id}_{buffer_number}-000.ts'
    if not os.path.isfile(buffer_file):
        print(buffer_file)
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

def handle_camera_action(cam_id):
    print(f"Handling action for {cam_id}")
    final_video = save_last_30_seconds_from_buffer(cam_id)
    if final_video:
        upload_to_google_cloud(final_video)

def main():
    upload_to_google_cloud("mg-belohorizonte-duna-cam3-03072024-100002.mp4")
    
if __name__ == "__main__":
    main()
