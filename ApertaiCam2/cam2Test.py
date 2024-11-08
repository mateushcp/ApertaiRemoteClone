import time
import subprocess
import os
from datetime import datetime
from google.cloud import storage
from gpiozero import Button
import shutil

# Configuration
STATE = "mg"
CITY = "belohorizonte"
COURT = "Sagrada Beach"
BUCKET_NAME = "videos-283812"
CREDENTIALS_PATH = "/home/abidu/Desktop/keys.json"
BUFFER_PATH = "/home/abidu/Desktop/ApertaiRemoteClone/ApertaiCam2"
QUEUE_DIR = "/home/abidu/Desktop/ApertaiRemoteClone"

def save_last_30_seconds_from_buffer():
    datetime_now = datetime.now()
    datetime_now_formatted = f"{datetime_now.day:02}{datetime_now.month:02}{datetime_now.year}-{datetime_now.hour:02}{datetime_now.minute:02}{datetime_now.second:02}"

    # Nomes de arquivos de saída para ambos os buffers
    output_file_name_1 = os.path.abspath(f"{STATE}-{CITY}-{COURT}-{datetime_now_formatted}b1.mp4")
    output_file_name_2 = os.path.abspath(f"{STATE}-{CITY}-{COURT}-{datetime_now_formatted}b2.mp4")
    
    # Arquivos de entrada para ambos os buffers
    input_file_1 = os.path.join(BUFFER_PATH, 'cam-2-buffer-1-000.ts')
    input_file_2 = os.path.join(BUFFER_PATH, 'cam-2-buffer-2-000.ts')
    
    # Comandos para salvar os últimos 30 segundos dos buffers
    save_command_1 = [
        'ffmpeg',
        '-sseof', '-30',  # Começa 30 segundos antes do final do arquivo
        '-i', input_file_1,
        '-c', 'copy',
        output_file_name_1
    ]
    
    save_command_2 = [
        'ffmpeg',
        '-sseof', '-30',  # Começa 30 segundos antes do final do arquivo
        '-i', input_file_2,
        '-c', 'copy',
        output_file_name_2
    ]
    
    # Executa os comandos para salvar ambos os buffers
    subprocess.run(save_command_1, check=True)
    subprocess.run(save_command_2, check=True)

    print(f"Saved last 30 seconds to {output_file_name_1}")
    print(f"Saved last 30 seconds to {output_file_name_2}")

    # Função para obter a duração de um vídeo com ffprobe
    def get_video_duration(file_path):
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return float(result.stdout)

    # Obtém a duração dos dois vídeos
    duration_1 = get_video_duration(output_file_name_1)
    duration_2 = get_video_duration(output_file_name_2)
    
    print(f"Duration of {output_file_name_1}: {duration_1} seconds")
    print(f"Duration of {output_file_name_2}: {duration_2} seconds")

    # Compara as durações e retorna o vídeo com maior duração
    if duration_1 > duration_2:
        print(f"Returning {output_file_name_1}")
        return output_file_name_1
    else:
        print(f"Returning {output_file_name_2}")
        return output_file_name_2

def upload_to_google_cloud(file_name):
    client = storage.Client.from_service_account_json(CREDENTIALS_PATH)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(os.path.basename(file_name).replace("-", "/"))
    blob.upload_from_filename(file_name, content_type='application/octet-stream')
    print(f"Uploaded {file_name} to {BUCKET_NAME}")
    os.remove(file_name)  # Clean up the local file

def save_to_queue(file_path):
    queue_file_path = os.path.join(QUEUE_DIR, os.path.basename(file_path))
    shutil.move(file_path, queue_file_path) 

def generate_thumbnail(video_path):
    thumbnail_path = video_path.replace(".mp4", ".jpg")
    command = [
        "ffmpeg",
        "-i", video_path,
        "-ss", "00:00:03",
        "-vframes", "1",
        "-q:v", "2",
        thumbnail_path
    ]
    try:
        subprocess.run(command, check=True)
        print(f"Thumbnail saved at: {thumbnail_path}")
        return thumbnail_path
    except subprocess.CalledProcessError as e:
        print("Error generating thumbnail:", e)
        return None

def main():
    button1 = Button(16)
    
    while True:
        
        if not button1.is_pressed:
            print("Saving last 30 seconds of video...")
            final_video = save_last_30_seconds_from_buffer()
            thumbnail = generate_thumbnail(final_video)
            save_to_queue(final_video)
            if thumbnail:
               upload_to_google_cloud(thumbnail)
            time.sleep(2.0)
        time.sleep(0.1)

if __name__ == "__main__":
    main()