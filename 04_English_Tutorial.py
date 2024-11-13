import os
import glob
import subprocess
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips

def ajustar_audio(audio_clip, duration):
    """Ajusta el audio para que coincida con la duración especificada"""
    audio_duration = audio_clip.duration
    if audio_duration < duration:
        # Repetir el audio en bucle si es más corto
        clips = [audio_clip] * int(duration // audio_duration) + [audio_clip.subclip(0, duration % audio_duration)]
        return concatenate_audioclips(clips)
    elif audio_duration > duration:
        # Recortar el audio si es más largo
        return audio_clip.subclip(0, duration)
    return audio_clip

def reemplazar_audio(video_path, audio_path, output_path):
    video_clip = None
    audio_clip = None
    try:
        print("🎬 Cargando el video y el audio...")

        # Cargar el video y el audio
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)

        # Ajustar el audio para que coincida con la duración del video
        video_duration = video_clip.duration
        audio_clip = ajustar_audio(audio_clip, video_duration)

        # Asignar el nuevo audio al video
        print("🔊 Asignando el nuevo audio al video...")
        video_clip = video_clip.set_audio(audio_clip)

        # Verificar soporte de GPU para NVIDIA
        try:
            result = subprocess.run(["ffmpeg", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            use_gpu = "h264_nvenc" in result.stdout
            print("🚀 Usando la GPU NVIDIA para la codificación del video.") if use_gpu else print("❌ Usando códec predeterminado en CPU.")
        except Exception as e:
            print(f"❌ Error al verificar la GPU: {e}")
            use_gpu = False

        # Definir códecs y formatos compatibles
        video_codec = "h264_nvenc" if use_gpu else "libx264"
        audio_codec = "aac"

        # Escribir el video con parámetros optimizados
        print(f"💾 Guardando el archivo con el nuevo audio como: {output_path}")
        video_clip.write_videofile(
            output_path,
            codec=video_codec,
            audio_codec=audio_codec,
            audio_bitrate="192k",
            threads=2,
            preset="medium" if use_gpu else "fast",
            ffmpeg_params=["-movflags", "faststart", "-pix_fmt", "yuv420p"]  # Configuración clave
        )
        print(f"✅ El archivo ha sido guardado exitosamente como {output_path}")
    except Exception as e:
        print(f"❌ Error al procesar el video: {e}")
    finally:
        # Cerrar los clips para liberar recursos
        if video_clip:
            video_clip.close()
        if audio_clip:
            audio_clip.close()

def procesar_archivos(video_folder, audio_folder, output_folder):
    if not os.path.exists(output_folder):
        print("📂 Creando la carpeta de salida...")
        os.makedirs(output_folder)

    print("🔍 Buscando archivos de video y audio...")
    videos = glob.glob(os.path.join(video_folder, "*.mp4"))
    audios = glob.glob(os.path.join(audio_folder, "*.mp3"))

    print("🎥 Archivos de video encontrados:")
    for video in videos:
        print(f"  - {os.path.basename(video)}")

    print("🎶 Archivos de audio encontrados:")
    for audio in audios:
        print(f"  - {os.path.basename(audio)}")

    for video_path in videos:
        video_filename = os.path.basename(video_path)
        fecha_video = video_filename.replace("_no_silence.mp4", "")

        # Crear el nombre esperado del archivo de audio
        expected_audio_name = f"{fecha_video}_no_silence_EN.mp3"
        matching_audio = os.path.join(audio_folder, expected_audio_name)

        if os.path.exists(matching_audio):
            output_path = os.path.join(output_folder, video_filename.replace("_no_silence", ""))
            print(f"🎥 Procesando video: {video_filename} con audio: {expected_audio_name}")
            reemplazar_audio(video_path, matching_audio, output_path)
        else:
            print(f"⚠️ No se encontró el archivo de audio correspondiente para el video {video_filename}")

# Configurar las rutas de las carpetas
video_folder = r"C:\Users\wmate\OneDrive\Trabajo\UDEMY\YOLO\Videos\Videos ES"
audio_folder = r"C:\Users\wmate\OneDrive\Trabajo\UDEMY\YOLO\Videos\Subtitulos"
output_folder = r"C:\Users\wmate\OneDrive\Trabajo\UDEMY\YOLO\Videos\Videos ES\Output"

# Ejecutar el procesamiento de los archivos
print("🚀 Iniciando el procesamiento de videos y audios...")
procesar_archivos(video_folder, audio_folder, output_folder)
print("✅ Proceso completado.")
