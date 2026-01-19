import asyncio
import os
from google import genai
import logging

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        try:
            with open('/home/cm4/robot-project/src/secrets.txt', 'r') as f:
                api_key = f.read().strip()
            # Naudojame tiesioginį klientą be v1beta prefiksų
            self.client = genai.Client(api_key=api_key)
        except:
            self.client = None

    async def monitor_wake_word(self):
        """Imituojame aktyvavimą kas 20s gynimui"""
        while True:
            await asyncio.sleep(20)
            yield True

    async def record_audio(self, duration=3):
        await asyncio.sleep(duration)
        return b"data"

    async def send_to_gemini(self, audio_data):
        if not self.client:
            return "API RAKTO KLAIDA"
        try:
            # Pakeistas modelio ID ir iškvieta
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents="Tu esi robotas Evil Sonic. Atsakyk lietuviškai, trumpai, grėsmingai į klausimą: Koks tavo planas?"
            )
            return response.text
        except Exception as e:
            return f"DI KLAIDA: {str(e)}"
