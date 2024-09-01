import time
import subprocess
import os
from datetime import datetime
from google.cloud import storage
from gpiozero import Button

# Configuration
STATE = "mg"
CITY = "belohorizonte"
COURT = "sagradaBeach"
BUCKET_NAME = "videos-283812"
CREDENTIALS_PATH = "/home/abidu/Desktop/keys.json"
BUFFER_PATH = "/home/abidu/Desktop/ApertaiRemoteClone/ApertaiCam2"

def save_last_30_seconds_from_buffer():
    datetime_now = datetime.now()
    datetime_now_formatted = f"{datetime_now.day:02}{datetime_now.month:02}{datetime_now.year}-{datetime_now.hour:02}{datetime_now.minute:02}{datetime_now.second:02}"
    output_file_name = os.path.abspath(f"{STATE}-{CITY}-{COURT}-{datetime_now_formatted}.mp4")
    
    # Determina qual buffer usar baseando-se no segundo atual
    seconds = datetime_now.second
    buffer_id = '2' if seconds < 30 else '1'
    input_file = os.path.join(BUFFER_PATH, f'cam-2-buffer-{buffer_id}-000.ts')
    
    # Comando para salvar os últimos 30 segundos do buffer
    save_command = [
        'ffmpeg',
        '-sseof', '-30',  # Start 30 seconds before the end of the file
        '-i', input_file,
        '-c', 'copy',
        output_file_name
    ]
    
    subprocess.run(save_command, check=True)
    print(f"Saved last 30 seconds to {output_file_name}")
    return output_file_name

def upload_to_google_cloud(file_name):
    client = storage.Client.from_service_account_json(CREDENTIALS_PATH)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(os.path.basename(file_name).replace("-", "/"))
    blob.upload_from_filename(file_name, content_type='application/octet-stream')
    print(f"Uploaded {file_name} to {BUCKET_NAME}")
    os.remove(file_name)  # Clean up the local file

def main():
    button1 = Button(26)
    
    while True:
        if not button1.is_pressed:
            print("Saving last 30 seconds of video...")
            final_video = save_last_30_seconds_from_buffer()
            upload_to_google_cloud(final_video)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
