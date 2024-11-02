import subprocess

# Função para rotacionar o vídeo e depois redimensionar, ajustar a opacidade e sobrepor imagens
def overlay_images_on_video(input_file, image_files, output_file, positions, image_size=(100, 100), opacity=0.7):
    # Lista de inputs para o FFmpeg
    inputs = ['-i', input_file]  # Input do vídeo original

    # Adiciona as imagens à lista de inputs
    for image in image_files:
        if image:  # Verifica se a imagem existe
            inputs += ['-i', image]

    # Filtro para rotacionar o vídeo 90 graus anti-horário
    filter_complex = "[0:v]transpose=2[rotated];"  # Rotação do vídeo

    # Constrói o filtro de redimensionamento, ajuste de opacidade e overlay das imagens
    current_stream = "[rotated]"
    for i, (x_offset, y_offset) in enumerate(positions):
        # Redimensiona e ajusta a opacidade da imagem
        filter_complex += f"[{i+1}:v]scale={image_size[0]}:{image_size[1]},format=rgba,colorchannelmixer=aa={opacity}[img{i}];"
        # Sobrepõe a imagem ajustada
        filter_complex += f"{current_stream}[img{i}]overlay={x_offset}:{y_offset}"
        if i < len(positions) - 1:
            filter_complex += f"[tmp{i}];"
            current_stream = f"[tmp{i}]"
        else:
            filter_complex += ";"  # Não adiciona mais saídas após o último overlay

    # Comando FFmpeg completo sem o parâmetro de áudio
    command = ['ffmpeg'] + inputs + ['-filter_complex', filter_complex, output_file]

    try:
        subprocess.run(command, check=True)
        print(f"Vídeo com overlay de imagens redimensionadas, opacidade ajustada e rotação concluído: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao processar o vídeo: {e}")

# Função principal para testar a sobreposição de imagens e rotação
def main():
    input_video = '/home/apertai/Desktop/ApertaiRemoteClone/mg_belohorizonte_Sagrada Beach_25102024_212652b1.mp4'
    output_video = '/home/apertai/Desktop/ApertaiRemoteClone/ApertaiCam3/video_with_image_overlay_and_rotation.mp4'
    
    # Caminhos das imagens que serão sobrepostas
    image_files = [
        '/home/apertai/Desktop/image1.png',  # Primeira imagem
        '/home/apertai/Desktop/image2.png',  # Segunda imagem
        '/home/apertai/Desktop/image3.png'   # Terceira imagem
    ]

    positions = [
        (10, 10),    # Imagem 0 no canto superior esquerdo
        (55, 1080),  # Imagem 1 no canto inferior esquerdo
        (500, 1080)  # Imagem 2 no canto inferior direito
    ]
    
    # Chama a função para sobrepor as imagens redimensionadas, ajustar a opacidade e rotacionar o vídeo
    overlay_images_on_video(input_video, image_files, output_video, positions, image_size=(160, 160), opacity=0.7)

if __name__ == "__main__":
    main()
