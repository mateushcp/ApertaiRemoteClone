import time
import subprocess
import os
from datetime import datetime
from google.cloud import storage
from gpiozero import Button

# Configuration
STATE = "mg"
CITY = "belohorizonte"
COURT = "Sagrada Beach"
BUCKET_NAME = "videos-283812"
CREDENTIALS_PATH = "/home/abidu/Desktop/keys.json"
BUFFER_PATH = "/home/abidu/Desktop/ApertaiRemoteClone/ApertaiCam2"
AD_IMAGES_BUCKET = "ad-images-214939"

ad_image_files = [
    f"/home/abidu/Downloads/image1.png",  # Primeira imagem (topo esquerdo)
    f"/home/abidu/Downloads/image2.png",  # Segunda imagem (rodapé)
    f"/home/abidu/Downloads/image3.png"   # Terceira imagem (rodapé)
]

bucket_images = [
    'mg/belohorizonte/sagradaBeach/cloud-image-1.png',  # Caminho da primeira imagem no bucket
    'mg/belohorizonte/sagradaBeach/patrocinador-2.png', # Caminho da segunda imagem no bucket
    'mg/belohorizonte/sagradaBeach/patrocinador-3.png'  # Caminho da terceira imagem no bucket
]

def download_image_from_bucket_if_not_exists(bucket_name, source_blob_name, destination_file_name, credentials_path):
    if os.path.exists(destination_file_name):
        print(f"Imagem {destination_file_name} já existe localmente. Pulando download.")
        return destination_file_name

    print(f"Baixando {destination_file_name} do bucket.")
    storage_client = storage.Client.from_service_account_json(credentials_path)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    if blob.exists():
        blob.download_to_filename(destination_file_name)
        return destination_file_name
    else:
        print(f"Imagem {source_blob_name} não encontrada no bucket.")
        return None

def convert_video_with_images(input_file, output_file, images):
    filter_complex = ""
    inputs = ['-i', input_file]
    
    if images[0]:
        filter_complex += "[1:v]scale=260:260[logo];[0:v][logo]overlay=10:10"
        inputs += ['-i', images[0]]
    
    for i, img in enumerate(images[1:], start=2):
        if img:
            inputs += ['-i', img]
            x_offset = 10 + (i - 2) * 40
            filter_complex += f";[{i}:v]scale=36:36,format=rgba,colorchannelmixer=aa=0.75[img{i}];[0:v][img{i}]overlay={x_offset}:main_h-46"
    
    if not filter_complex:
        return input_file  # Retorna o vídeo original se não houver imagens de patrocínio
    
    command = ['ffmpeg'] + inputs + ['-filter_complex', filter_complex, output_file]
    subprocess.run(command, check=True)
    return output_file

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

def main():
    button1 = Button(26)

    downloaded_images = []
    for bucket_image, local_image in zip(bucket_images, ad_image_files):
        downloaded_image = download_image_from_bucket_if_not_exists(AD_IMAGES_BUCKET, bucket_image, local_image, CREDENTIALS_PATH)
        downloaded_images.append(downloaded_image)
    
    while True:
        if not button1.is_pressed:
            print("Saving last 30 seconds of video...")
            final_video = save_last_30_seconds_from_buffer()

            final_video_with_ads = f"{final_video[:-4]}_ads.mp4"
            final_video_with_ads = convert_video_with_images(final_video, final_video_with_ads, downloaded_images)

            upload_to_google_cloud(final_video_with_ads)
        time.sleep(2.0)

if __name__ == "__main__":
    main()
