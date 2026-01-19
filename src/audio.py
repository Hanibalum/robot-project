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
        
        # 1. Gemini krovimas
        try:
            with open(os.path.join(BASE_DIR, "secrets.txt"), "r") as f:
                api_key = f.read().strip()
            self.client = genai.Client(api_key=api_key)
            self.logger.info("Gemini API raktas užkrautas.")
        except:
            self.client = None

        # 2. Vosk (Išjungtas, jei nėra failų, kad netrukdytų)
        self.recognizer = None
        if os.path.exists(model_path):
            try:
                self.model = vosk.Model(model_path)
                self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            except: pass

    async def monitor_wake_word(self):
        """Imituojame aktyvavimą kas 25 sekundes gynimui"""
        while True:
            await asyncio.sleep(25)
            yield True

    async def record_audio(self, duration=3):
        await asyncio.sleep(duration)
        return b"raw"

    async def send_to_gemini(self, audio_data):
        if not self.client: return "DI modelis nepasiekiamas."
        try:
            # NAUJAS SDK reikalauja paprasto modelio vardo
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-1.5-flash",
                contents="Tu esi Evil Sonic. Atsakyk trumpai, lietuviskai, piktai."
            )
            return response.text
        except Exception as e:
            return "DI RYSIO KLAIDA"
