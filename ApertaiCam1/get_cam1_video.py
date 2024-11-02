import time
import subprocess
import os
from datetime import datetime
from google.cloud import storage
from gpiozero import Button
import sys

# Configuration
STATE = "mg"
CITY = "belohorizonte"
COURT = "Sagrada Beach"
USER = "apertai" # Usuário utilizado na hora de configurar a imagem do Raspberry (pode ser encontrado na tabela "Configurações do cliente")
# 

BUTTON_COOLDOWN = 2.0

BUCKET_NAME = "videos-283812"
CREDENTIALS_PATH = f"/home/{USER}/Desktop/keys.json"
BUFFER_PATH = f"/home/{USER}/Desktop/ApertaiRemoteClone/ApertaiCam1"

def save_last_30_seconds_from_buffer():
    datetime_now = datetime.now()
    datetime_now_formatted = f"{datetime_now.day:02}{datetime_now.month:02}{datetime_now.year}-{datetime_now.hour:02}{datetime_now.minute:02}{datetime_now.second:02}"

    # Nomes de arquivos de saída para ambos os buffers
    output_file_name_1 = os.path.abspath(f"{STATE}-{CITY}-{COURT}-{datetime_now_formatted}b1-temporary.mp4")
    output_file_name_2 = os.path.abspath(f"{STATE}-{CITY}-{COURT}-{datetime_now_formatted}b2-temporary.mp4")
    
    # Arquivos de entrada para ambos os buffers
    input_file_1 = os.path.join(BUFFER_PATH, 'cam-1-buffer-1-000.ts')
    input_file_2 = os.path.join(BUFFER_PATH, 'cam-1-buffer-2-000.ts')
    
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
        os.remove(output_file_name_2) # Clean up the local file
        return output_file_name_1
    else:
        print(f"Returning {output_file_name_2}")
        os.remove(output_file_name_1) # Clean up the local file
        return output_file_name_2 

def upload_to_google_cloud(file_name):
    client = storage.Client.from_service_account_json(CREDENTIALS_PATH)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(os.path.basename(file_name).replace("-", "/"))
    blob.upload_from_filename(file_name, content_type='application/octet-stream')
    print(f"Uploaded {file_name} to {BUCKET_NAME}")
    os.remove(file_name)  # Clean up the local file

def main():
    button1 = Button(24)
    
    while True:
        if not button1.is_pressed:
            print("Saving last 30 seconds of video...")
            temporary_video_file_name = save_last_30_seconds_from_buffer()
            final_video_file_name = overlay_images_on_video(temporary_video_file_name)
            upload_to_google_cloud(final_video_file_name)
            time.sleep(BUTTON_COOLDOWN)
        time.sleep(0.1)





IMAGE_FILES = ["/home/apertai/Desktop/ApertaiRemoteClone/Sponsor/image1.png", "/home/apertai/Desktop/ApertaiRemoteClone/Sponsor/image2.png", "/home/apertai/Desktop/ApertaiRemoteClone/Sponsor/image3.png", "/home/apertai/Desktop/ApertaiRemoteClone/Sponsor/image4.png"]
POSITIONS = [(10, 10), (45, 1630), (790, 1630), (790, 15)] 
IMAGE_SIZE = (250, 250)
OPACITY = 0.8

def overlay_images_on_video(temporary_video_file_name):
    output_video_file_name = getFinalVideoName(temporary_video_file_name)

    start_time = time.time()
    process = psutil.Process(os.getpid())

    inputs = ['-i', temporary_video_file_name]
    for image in IMAGE_FILES:
        if image:
            inputs += ['-i', image]
    filter_complex = "[0:v]transpose=2[rotated];"
    current_stream = "[rotated]"
    for i, (x_offset, y_offset) in enumerate(POSITIONS):
        filter_complex += f"[{i+1}:v]scale={IMAGE_SIZE[0]}:{IMAGE_SIZE[1]},format=rgba,colorchannelmixer=aa={OPACITY}[img{i}];"
        filter_complex += f"{current_stream}[img{i}]overlay={x_offset}:{y_offset}"
        if i < len(POSITIONS) - 1:
            filter_complex += f"[tmp{i}];"
            current_stream = f"[tmp{i}]"
        else:
            filter_complex += ""
    command = ['ffmpeg', '-threads', '1'] + inputs + ['-filter_complex', filter_complex, output_video_file_name]
    
    try:
        process = subprocess.Popen(command, check=True) # Troquei para popen para conseguir finalizar o processo
        process.wait() # Adicionei wait para esperar o processo terminar
        print(f"Vídeo processado com sucesso: {output_video_file_name}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao processar o vídeo: {e}")
    finally:
        if process and process.poll() is None:  # Adicionei para verificar se o processo ainda existe
            process.terminate() # Adicionei para garantir que o processo foi finalizado
    
    # Monitoramento de tempo, memória e CPU
    elapsed_time = time.time() - start_time
    memory_info = process.memory_info()
    cpu_usage = process.cpu_percent(interval=1)

    print(f"Tempo de execução: {elapsed_time:.2f} segundos")
    print(f"Memória usada: {memory_info.rss / (1024 * 1024):.2f} MB")
    print(f"Uso de CPU: {cpu_usage}%")
    
    # Monitoramento de GPU (se disponível)
    try:
        gpu_usage = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"]
        ).decode("utf-8").strip()
        print(f"Uso de GPU: {gpu_usage}%")
    except FileNotFoundError:
        print("GPU não detectada ou `nvidia-smi` não está disponível.")


def getFinalVideoName(temporary_video_file_name):
    return temporary_video_file_name.replace("-temporary", "")




if __name__ == "__main__":
    main()