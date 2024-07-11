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
BUCKET_NAME = "apertai-cloud"
CREDENTIALS_PATH = "/home/apertai/Desktop/apertaiKeys.json"

# Define camera URLs (initially empty, to be filled with discovered IPs)
cameras = {}

# Setup for recording and buttons
buffers = {}
start_times = {}
buttons = {
    "button1": Button(25),
    "button2": Button(24),
    "button3": Button(23)
}

def start_buffer_stream(rtsp_url, buffer_number):
    print(f"Starting buffer {buffer_number} for URL {rtsp_url} at {datetime.now()}")
    buffer_command = [
        'ffmpeg',
        '-i', rtsp_url,
        '-map', '0',
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', '60',
        '-segment_wrap', '1',
        '-reset_timestamps', '1',
        f'buffer{buffer_number}-%03d.ts'
    ]
    return subprocess.Popen(buffer_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_buffer_streams():
    for cam_id, url in cameras.items():
        buffers[cam_id] = {'buffer1': start_buffer_stream(url, 1)}
        start_times[cam_id] = datetime.now()

    time.sleep(30)

    for cam_id, url in cameras.items():
        buffers[cam_id]['buffer2'] = start_buffer_stream(url, 2)

def save_last_30_seconds_from_buffer(cam_id, datetime_start_recording):
    datetime_now = datetime.now()
    datetime_now_formatted = f"{datetime_now.day:02}{datetime_now.month:02}{datetime_now.year}-{datetime_now.hour:02}{datetime_now.minute:02}{datetime_now.second:02}"
    output_file_name = os.path.abspath(f"{STATE}-{CITY}-{COURT}-{cam_id}-{datetime_now_formatted}.mp4")
    
    diff = datetime_now - datetime_start_recording
    seconds_diff = diff.seconds % 60

    buffer_key = 'buffer2' if seconds_diff < 30 else 'buffer1'
    buffer_file = buffers[cam_id][buffer_key].name  # Assuming you're storing the process and file names

    save_command = [
        'ffmpeg',
        '-sseof', '-30',
        '-i', f'{buffer_file}',
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
    rtsp_devices = get_rtsp_ips()  # Descobre os IPs das câmeras RTSP
    # Atualiza as URLs das câmeras com os novos IPs
    for i, ip in enumerate(rtsp_devices):
        cameras[f"cam{i+1}"] = f"rtsp://apertaiCam{i+1}:130355va@{ip}/stream1"

    start_buffer_streams()  # Inicia a gravação

    while True:
        for button_id, button in buttons.items():
            cam_id = button_id.replace("button", "cam")
            if not button.is_pressed:
                final_video = save_last_30_seconds_from_buffer(cam_id, start_times[cam_id])
                upload_to_google_cloud(final_video)

if __name__ == "__main__":
    main()
