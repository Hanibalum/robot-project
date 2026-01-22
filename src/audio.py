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
            
            # PRIVERSTINIS v1 NAUDOJIMAS (ištaisys 404 klaidą)
            self.client = genai.Client(
                api_key=api_key, 
                http_options={'api_version': 'v1'}
            )
            self.logger.info("Gemini paruoštas per v1 sąsają.")
        except Exception as e:
            self.logger.error(f"Klaida krovime: {e}")
            self.client = None

    async def monitor_wake_word(self):
        while True:
            await asyncio.sleep(20) # Gynimo demo ciklas
            yield True

    async def record_audio(self, duration=3):
        await asyncio.sleep(duration)
        return b"raw"

    async def send_to_gemini(self, audio_data):
        if not self.client: return "API RAKTO KLAIDA"
        try:
            # Užklausa be models/ prefixo
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents="Tu esi piktas Sonic. Atsakyk lietuviškai, trumpai."
            )
            return response.text
        except Exception as e:
            return f"DI TRIKDIS: {str(e)[:50]}"
