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

def start_buffer_stream(buffer_number, cam_id):
    print(f"Starting buffer {buffer_number} for {cam_id} at {datetime.now()}")
    buffer_file = f'{cam_id}_buffer{buffer_number}-%03d.ts'
    buffer_command = [
        'ffmpeg',
        '-i', cameras[cam_id],
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',
        '-segment_wrap', '1',
        '-reset_timestamps', '1',
        buffer_file
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE), buffer_file

def test_buffer_creation(cam_id, buffer_info):
    buffer_file = buffer_info['file'].replace('%03d', '000')
    if os.path.exists(buffer_file):
        print(f"Buffer {buffer_file} for {cam_id} was created successfully.")
    else:
        print(f"Error: Buffer {buffer_file} for {cam_id} was not created correctly.")

def start_buffer_streams():
    buffers = {}
    
    for cam_id in cameras.keys():
        # Start the first buffer for the camera
        buffers[cam_id] = {
            'buffer1': start_buffer_stream(1, cam_id)
        }
        
        # Test the first buffer creation
        test_buffer_creation(cam_id, buffers[cam_id]['buffer1'])
        
        # Wait for 30 seconds before starting the second buffer
        print(f"Waiting for 30 seconds before starting buffer 2 for camera {cam_id}...")
        time.sleep(30)
        
        # Start the second buffer for the camera
        buffers[cam_id]['buffer2'] = start_buffer_stream(2, cam_id)
        
        # Test the second buffer creation
        test_buffer_creation(cam_id, buffers[cam_id]['buffer2'])
    
    return buffers

def save_last_30_seconds_from_buffer(cam_id, datetime_start_recording):
    datetime_now = datetime.now()
    datetime_now_formatted = f"{datetime_now.day:02}{datetime_now.month:02}{datetime_now.year}-{datetime_now.hour:02}{datetime_now.minute:02}{datetime_now.second:02}"
    output_file_name = os.path.abspath(f"{STATE}-{CITY}-{COURT}-{cam_id}-{datetime_now_formatted}.mp4")
    
    diff = datetime_now - datetime_start_recording
    seconds_diff = diff.seconds % 60

    buffer_number = 2 if seconds_diff < 30 else 1
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

    # # Update camera URLs with new IPs
    # for i, ip in enumerate(rtsp_devices):
    #     cameras[f"cam{i+1}"] = f"rtsp://apertaiCam{i+1}:130355va@{ip}/stream1"

    buffers = start_buffer_streams()  # Start recording and verify if all buffers were created
    if not buffers:
        print("Error: Not all buffers were created successfully.")
        return

    while True:
        for button_id, button in buttons.items():
            cam_id = button_id.replace("button", "cam")
            if button.is_pressed:
                final_video = save_last_30_seconds_from_buffer(cam_id, start_times[cam_id])
                upload_to_google_cloud(final_video)

if __name__ == "__main__":
    main()
