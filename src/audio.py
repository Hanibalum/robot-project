import asyncio
import os
import logging
import google.generativeai as genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        try:
            with open(os.path.join(BASE_DIR, "secrets.txt"), "r") as f:
                api_key = f.read().strip()
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("Gemini sukonfiguruotas per stabilu SDK.")
        except Exception as e:
            self.logger.error(f"Klaida: {e}")
            self.model = None

        self.recognizer = None

    async def monitor_wake_word(self):
        while True:
            await asyncio.sleep(20)
            yield True

    async def record_audio(self, duration=3):
        await asyncio.sleep(duration)
        return "voice_data"

    async def send_to_gemini(self, audio_data):
        if not self.model: return "API KLAIDA"
        try:
            # Senuoju būdu, kuris visada veikia
            response = await asyncio.to_thread(
                self.model.generate_content,
                "Tu esi Evil Sonic robotas. Atsakyk lietuviskai, trumpai, piktas."
            )
            return response.text
        except Exception as e:
            return f"DI KLAIDA: {e}"
