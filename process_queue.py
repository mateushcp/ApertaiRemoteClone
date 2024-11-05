import os
import time
import subprocess
from google.cloud import storage

QUEUE_DIR = "/home/abidu/Desktop/temp/ApertaiRemoteClone"
CREDENTIALS_PATH = "/home/abidu/Desktop/keys.json"
BUCKET_NAME = "videos-283812"

def overlay_images_on_video(input_file, image_files, output_file, positions, image_size=(100, 100), opacity=0.7):
    start_time = time.time()

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
    command = ['ffmpeg', '-threads', '1'] + inputs + ['-filter_complex', filter_complex, '-threads', '2', output_file]
    
    try:
        subprocess.run(command, check=True)
        print(f"Vídeo processado com sucesso: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao processar o vídeo: {e}")

def process_and_upload_video():
    client = storage.Client.from_service_account_json(CREDENTIALS_PATH)
    bucket = client.bucket(BUCKET_NAME)
    
    while True:
        # Verifica se há arquivos no diretório de fila
        queue_files = [f for f in os.listdir(QUEUE_DIR) if f.endswith(".mp4")]
        
        if queue_files:
            video_file = os.path.join(QUEUE_DIR, queue_files[0])  # Pega o primeiro vídeo na fila
            
            # Define o caminho de saída após o processamento com o mesmo nome do arquivo de entrada
            output_file = os.path.join(QUEUE_DIR, "processed_" + os.path.basename(video_file))
            
            # Processa o vídeo com a função overlay_images_on_video
            overlay_images_on_video(
                video_file,
                ["/path/to/image1.png", "/path/to/image2.png", "/path/to/image3.png"],
                output_file,
                [(10, 10), (35, 1630), (800, 1630)],
                image_size=(250, 250),
                opacity=0.8
            )
            
            # Faz upload para o Google Cloud Storage
            blob = bucket.blob(os.path.basename(video_file).replace("-", "/"))
            blob.upload_from_filename(output_file, content_type='application/octet-stream')
            print(f"Uploaded {output_file} to {BUCKET_NAME}")
            
            # Remove os arquivos locais
            os.remove(video_file)
            os.remove(output_file)
            print(f"Processed and deleted {video_file} and {output_file}.")
        else:
            time.sleep(1)  # Aguarda um momento antes de verificar novamente a fila


if __name__ == "__main__":
    process_and_upload_video()
