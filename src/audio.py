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
            self.logger.info("Gemini paruoštas.")
        except:
            self.client = None

    async def monitor_wake_word(self):
        while True:
            await asyncio.sleep(20)
            yield True

    async def send_to_gemini(self, audio_data):
        if not self.client: return "API ERROR"
        try:
            # PRIDĖTAS models/ prefixas, kuris būtinas v1 endpointui
            response = self.client.models.generate_content(
                model="models/gemini-1.5-flash",
                contents="Tu esi piktas Sonic. Atsakyk lietuviškai, labai trumpai."
            )
            return response.text
        except Exception as e:
            # Jei vis tiek meta klaidą, bandom be prefixo
            try:
                response = self.client.models.generate_content(model="gemini-1.5-flash", contents="Hi")
                return response.text
            except:
                return f"DI KLAIDA"
