import os
import sys
from src.services.video_service import add_audio_to_video

# URLs de prueba
VIDEO_URL = "https://filesamples.com/samples/video/mp4/sample_640x360.mp4"
AUDIO_URL = "https://filesamples.com/samples/audio/mp3/sample3.mp3"

# Llama a la función directamente
try:
    print("Iniciando prueba...")
    result = add_audio_to_video(VIDEO_URL, AUDIO_URL)
    print(f"Éxito! Resultado: {result}")
except Exception as e:
    print(f"Error durante la prueba: {str(e)}")
    import traceback
    traceback.print_exc()
