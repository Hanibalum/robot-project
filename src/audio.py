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
            # Naudojame modelį be papildomų prefixų
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("[OK] Gemini paruoštas stabiliai.")
        except:
            self.model = None

    async def monitor_wake_word(self):
        while True:
            await asyncio.sleep(25)
            yield True

    async def record_audio(self, duration=3):
        await asyncio.sleep(duration)
        return "data"

    async def send_to_gemini(self, audio_data):
        if not self.model: return "API RAKTO KLAIDA"
        try:
            # Tikslus užklausos formatas
            response = await asyncio.to_thread(self.model.generate_content, "Atsakyk trumpai lietuviškai.")
            return response.text
        except Exception as e:
            # Jei vis tiek 404, bandom kitą ID
            try:
                self.model = genai.GenerativeModel('gemini-pro')
                response = await asyncio.to_thread(self.model.generate_content, "Labas")
                return response.text
            except:
                return f"DI TRIKDIS: {str(e)[:30]}"
