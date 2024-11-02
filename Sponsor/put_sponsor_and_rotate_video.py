import subprocess
import sys
import time
import psutil
import os

IMAGE_FILES = ["image1.png", "image2.png", "image3.png", "image4.png"]
POSITIONS = [(10, 10), (35, 1630), (800, 1630), (800, 10)] # Checar posições originais, pq a ultima eu deduzi... !!!!!
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