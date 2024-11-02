import subprocess
import sys
import time
import psutil
import os

def overlay_images_on_video(input_file, image_files, output_file, positions, image_size=(100, 100), opacity=0.7):
    start_time = time.time()
    process = psutil.Process(os.getpid())

    inputs = ['-i', input_file]
    for image in image_files:
        if image:
            inputs += ['-i', image]
    filter_complex = "[0:v]transpose=2[rotated];"
    current_stream = "[rotated]"
    for i, (x_offset, y_offset) in enumerate(positions):
        filter_complex += f"[{i+1}:v]scale={image_size[0]}:{image_size[1]},format=rgba,colorchannelmixer=aa={opacity}[img{i}];"
        filter_complex += f"{current_stream}[img{i}]overlay={x_offset}:{y_offset}"
        if i < len(positions) - 1:
            filter_complex += f"[tmp{i}];"
            current_stream = f"[tmp{i}]"
        else:
            filter_complex += ""
    command = ['ffmpeg'] + inputs + ['-filter_complex', filter_complex, output_file]
    
    try:
        subprocess.run(["cpulimit", "-l", "50", "--"] + command, check=True)
        print(f"Vídeo processado com sucesso: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao processar o vídeo: {e}")
    
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

if __name__ == "__main__":
    input_video = sys.argv[1]
    image_files = sys.argv[2:5]
    output_video = sys.argv[5]
    
    positions = [(10, 10), (35, 1630), (800, 1630)]
    overlay_images_on_video(input_video, image_files, output_video, positions, image_size=(250, 250), opacity=0.8)
