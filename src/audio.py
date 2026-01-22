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
            
            # NAUDOJAME v1beta - tai vienintelis būdas išvengti 404 tavo aplinkoje
            self.client = genai.Client(
                api_key=api_key,
                http_options={'api_version': 'v1beta'}
            )
            self.logger.info("Gemini paruoštas per v1beta sąsają.")
        except Exception as e:
            self.logger.error(f"Klaida: {e}")
            self.client = None

    async def monitor_wake_word(self):
        """Tikrasis balso monitorius (bus pildomas su Vosk)"""
        while True:
            await asyncio.sleep(25) # Kol kas demo ciklas
            yield True

    async def record_audio(self, duration=3):
        """Garsas įrašomas čia (placeholder)"""
        await asyncio.sleep(duration)
        return b"raw_data"

    async def send_to_gemini(self, audio_data):
        if not self.client: return "API KEY ERROR"
        try:
            # Svarbu: modelio vardas be 'models/' prefixo naujame SDK
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents="Tu esi Evil Sonic. Atsakyk lietuviškai, trumpai, grėsmingai."
            )
            return response.text
        except Exception as e:
            self.logger.error(f"DI klaida: {e}")
            return "DI RYŠIO TRIKDIS"
