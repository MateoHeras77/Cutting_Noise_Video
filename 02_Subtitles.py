import torch
import whisper
import os
from pathlib import Path
from glob import glob

def write_srt(segments, file):
    """
    Escribe subtítulos en formato .srt a partir de los segmentos proporcionados.
    
    Args:
        segments (list): Lista de segmentos con 'start', 'end', y 'text'.
        file (file object): Objeto de archivo donde se escribirán los subtítulos.
    """
    for i, segment in enumerate(segments):
        # Escribir el número de secuencia
        file.write(f"{i + 1}\n")
        
        # Convertir el tiempo de inicio y fin a formato horas:minutos:segundos,milisegundos
        start = segment['start']
        end = segment['end']
        start_time = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02},{int((start * 1000) % 1000):03}"
        end_time = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02},{int((end * 1000) % 1000):03}"
        
        # Escribir el rango de tiempo
        file.write(f"{start_time} --> {end_time}\n")
        
        # Escribir el texto del segmento
        file.write(f"{segment['text']}\n\n")

def generate_subtitles(video_path):
    """
    Genera subtítulos en formato .srt para un video usando Whisper
    
    Args:
        video_path (str): Ruta al archivo de video
    
    Returns:
        str: Ruta del archivo de subtítulos generado
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"No se encontró el archivo: {video_path}")
        
        # Verificar si hay GPU disponible
        device = "cuda" if torch.cuda.is_available() else "cpu"
        gpu_status = "🚀 GPU activada" if device == "cuda" else "💻 Procesando en CPU"
        print(f"{gpu_status} - Usando dispositivo: {device}")
        
        # Cargar el modelo de Whisper
        print("🔄 Cargando modelo de Whisper... Por favor espera.")
        model = whisper.load_model("medium", device=device)
        print("✅ Modelo cargado exitosamente.")
        
        # Transcribir el video
        print(f"🎙️ Iniciando transcripción del video: {video_path}")
        result = model.transcribe(video_path)
        
        # Generar ruta de salida con extensión .srt
        output_path = Path(video_path).with_suffix('.srt')
        
        # Guardar subtítulos en formato .srt
        print(f"💾 Guardando subtítulos en: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            write_srt(result["segments"], f)
                
        print("🎉 ¡Subtítulos generados exitosamente!")
        return str(output_path)
        
    except Exception as e:
        print(f"❌ Error al generar subtítulos para {video_path}: {str(e)}")
        raise

if __name__ == "__main__":
    # Ruta de la carpeta con el patrón de archivos de video
    VIDEO_DIR = r"C:\Users\wmate\OneDrive\Trabajo\UDEMY\YOLO\Videos\*no_silence.mp4"
    
    # Obtener lista de todos los archivos que coinciden con el patrón
    video_files = glob(VIDEO_DIR)
    
    if not video_files:
        print("🔍 No se encontraron archivos que coincidan con el patrón.")
    else:
        print(f"📝 Encontrados {len(video_files)} archivos para procesar.")
        for video_path in video_files:
            try:
                print(f"\n🔹 Procesando archivo: {video_path}")
                subtitle_path = generate_subtitles(video_path)
                print(f"✅ Subtítulos guardados en: {subtitle_path}")
            except Exception as e:
                print(f"❌ Error en el procesamiento del archivo {video_path}: {str(e)}")
        print("\n🏁 Procesamiento completado para todos los archivos.")
