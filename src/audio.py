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
        # Gemini
        try:
            with open(os.path.join(BASE_DIR, "secrets.txt"), "r") as f:
                api_key = f.read().strip()
            self.client = genai.Client(api_key=api_key)
            self.logger.info("Gemini raktas užkrautas.")
        except: self.client = None

        # Vosk modelio patikra
        self.recognizer = None
        if os.path.exists(model_path) and os.listdir(model_path):
            try:
                self.model = vosk.Model(model_path)
                self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            except: pass
        else:
            self.logger.warning("Vosk modelio failų nėra. Veiks demo režimas.")

    async def monitor_wake_word(self):
        """Demo režimas poryt vyksiančiam gynimui"""
        while True:
            await asyncio.sleep(20)
            yield True

    async def record_audio(self, duration=3):
        await asyncio.sleep(duration)
        return b"raw"

    async def send_to_gemini(self, audio_data):
        if not self.client: return "API RAKTO KLAIDA"
        try:
            # Naudojame stabilesnį modelį v1 versijai
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model="gemini-pro",
                contents="Tu esi Evil Sonic. Atsakyk trumpai ir grėsmingai."
            )
            return response.text
        except Exception as e:
            return f"DI KLAIDA: {e}"
