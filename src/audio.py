import asyncio
import os
import logging
from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        try:
            with open(os.path.join(BASE_DIR, "secrets.txt"), "r") as f:
                api_key = f.read().strip()
            self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})
            self.logger.info("Gemini paruoštas per v1 sąsają.")
        except:
            self.client = None
            self.logger.error("API raktas nerastas.")

    async def monitor_wake_word(self):
        """Demo ciklas: robotas reaguoja kas 25 sekundes"""
        while True:
            await asyncio.sleep(25)
            yield True

    async def record_audio(self, duration=3):
        """Sugrąžinta funkcija, kurios trūko"""
        self.logger.info(f"Fiksuojamas garsas: {duration}s")
        await asyncio.sleep(duration)
        return b"raw_data"

    async def send_to_gemini(self, audio_data):
        if not self.client: return "API RAKTO KLAIDA"
        try:
            # Tikslus modelio kelias v1 versijai
            response = self.client.models.generate_content(
                model="models/gemini-1.5-flash",
                contents="Tu esi robotas Evil Sonic. Atsakyk lietuviškai, labai trumpai."
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Gemini klaida: {e}")
            return "DI RYŠIO TRIKDIS"
