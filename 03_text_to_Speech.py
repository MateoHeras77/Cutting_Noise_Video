import os
import re
import logging
from dataclasses import dataclass
from typing import List, Optional
from googletrans import Translator

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audio_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SubtitleEntry:
    """Estructura de datos para cada entrada de subtítulo"""
    index: int
    start_time: str
    end_time: str
    spanish_text: str
    english_text: Optional[str] = None
    start_ms: int = 0
    end_ms: int = 0
    duration_ms: int = 0

class AudioSynchronizer:
    def __init__(self, input_folder: str, output_folder: str):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.translator = Translator()
        self.entries: List[SubtitleEntry] = []

    def parse_timestamp(self, timestamp: str) -> int:
        """Convierte timestamp SRT a milisegundos"""
        hours, minutes, seconds = timestamp.split(':')
        seconds, milliseconds = seconds.split(',')
        return (int(hours) * 3600000 + 
                int(minutes) * 60000 + 
                int(seconds) * 1000 + 
                int(milliseconds))

    def parse_srt(self, file_path: str) -> None:
        """Lee y parsea el archivo SRT"""
        logger.info(f"Parseando archivo: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.*?\n)*?)\n'
        matches = re.finditer(pattern, content, re.MULTILINE)

        self.entries = []
        for match in matches:
            start_time = match.group(2)
            end_time = match.group(3)
            entry = SubtitleEntry(
                index=int(match.group(1)),
                start_time=start_time,
                end_time=end_time,
                spanish_text=match.group(4).strip(),
                start_ms=self.parse_timestamp(start_time),
                end_ms=self.parse_timestamp(end_time)
            )
            entry.duration_ms = entry.end_ms - entry.start_ms
            self.entries.append(entry)

        # Ordenar por tiempo de inicio
        self.entries.sort(key=lambda x: x.start_ms)
        logger.info(f"Procesados {len(self.entries)} subtítulos")

    def translate_entries(self) -> None:
        """Traduce todos los subtítulos al inglés"""
        logger.info("Traduciendo subtítulos...")
        for entry in self.entries:
            try:
                translation = self.translator.translate(entry.spanish_text, dest='en')
                entry.english_text = translation.text
                logger.debug(f"Traducido: {entry.spanish_text} -> {entry.english_text}")
            except Exception as e:
                logger.error(f"Error traduciendo subtítulo {entry.index}: {e}")
                entry.english_text = entry.spanish_text

    def save_translated_srt(self, output_srt_path: str) -> None:
        """Guarda los subtítulos traducidos en un archivo SRT."""
        logger.info(f"Guardando subtítulos traducidos en: {output_srt_path}")
        
        with open(output_srt_path, 'w', encoding='utf-8') as file:
            for entry in self.entries:
                file.write(f"{entry.index}\n")
                file.write(f"{entry.start_time} --> {entry.end_time}\n")
                file.write(f"{entry.english_text}\n\n")
        logger.info(f"Subtítulos traducidos guardados en: {output_srt_path}")

def main():
    input_folder = r"C:\Users\wmate\OneDrive\Trabajo\UDEMY\YOLO\Videos\Subtitulos"
    output_folder = input_folder

    try:
        for file_name in os.listdir(input_folder):
            if not file_name.endswith("_no_silence.srt"):
                continue

            logger.info(f"Procesando archivo: {file_name}")
            
            # Crear instancia del sincronizador
            syncer = AudioSynchronizer(input_folder, output_folder)
            
            # Procesar archivo SRT
            srt_path = os.path.join(input_folder, file_name)
            syncer.parse_srt(srt_path)
            
            # Traducir subtítulos
            syncer.translate_entries()
            
            # Guardar subtítulos traducidos
            translated_srt_path = os.path.join(output_folder, f"{os.path.splitext(file_name)[0]}_EN.srt")
            syncer.save_translated_srt(translated_srt_path)

    except Exception as e:
        logger.error(f"Error en el proceso principal: {e}")
        raise

if __name__ == "__main__":
    main()
