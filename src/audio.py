import sounddevice as sd
import vosk
import json
import logging
import asyncio
import os
from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self, model_path="/home/cm4/robot-project/src/model"):
        self.logger = logging.getLogger("AudioBrain")
        
        # 1. Gemini API konfigūravimas
        try:
            key_path = os.path.join(BASE_DIR, "secrets.txt")
            with open(key_path, "r") as f:
                api_key = f.read().strip()
            self.client = genai.Client(api_key=api_key)
            self.logger.info("Gemini API raktas užkrautas.")
        except:
            self.logger.error("API raktas nerastas secrets.txt")
            self.client = None

        # 2. Vosk modelis
        try:
            self.model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        except:
            self.logger.warning("Vosk modelis nerastas, veiks simuliacija.")
            self.recognizer = None

    async def monitor_wake_word(self):
        """Imituojame balso aktyvavimą kas 25s gynimui"""
        while True:
            await asyncio.sleep(25)
            yield True

    async def record_audio(self, duration=3):
        self.logger.info(f"Fiksuojamas garsas: {duration}s")
        await asyncio.sleep(duration)
        return b"raw_data"

    async def send_to_gemini(self, audio_data):
        """Siunčiame užklausą į Gemini"""
        if not self.client:
            return "DI nepasiekiamas."
        
        try:
            # Pataisytas kreipimasis į modelį pagal naują biblioteką
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-1.5-flash",
                contents="Atsakyk lietuviškai, trumpai, piktokai."
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Gemini klaida: {e}")
            return "DI RYŠIO TRIKDIS"
