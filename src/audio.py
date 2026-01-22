import asyncio
import os
import logging
from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        try:
            key_path = os.path.join(BASE_DIR, "secrets.txt")
            with open(key_path, "r") as f:
                api_key = f.read().strip()
            # Naudojame numatytuosius nustatymus, kad SDK pats parinktų versiją
            self.client = genai.Client(api_key=api_key)
            self.logger.info("Gemini paruoštas.")
        except Exception as e:
            self.logger.error(f"API rakto klaida: {e}")
            self.client = None

        self.recognizer = None

    async def monitor_wake_word(self):
        """Demo ciklas gynimui"""
        while True:
            await asyncio.sleep(25)
            yield True

    async def record_audio(self, duration=3):
        self.logger.info("Klausausi balso...")
        await asyncio.sleep(duration)
        return b"raw_data"

    async def send_to_gemini(self, audio_data):
        if not self.client: return "API RAKTO KLAIDA"
        
        # --- AUTOMATINIS MODELIŲ PERJUNGIMAS ---
        # Išbandome visus įmanomus pavadinimus, kad išvengtume 404 klaidos
        models_to_try = ["gemini-1.5-flash", "gemini-pro", "models/gemini-1.5-flash"]
        
        for model_name in models_to_try:
            try:
                self.logger.info(f"Bandomas modelis: {model_name}")
                response = self.client.models.generate_content(
                    model=model_name,
                    contents="Tu esi robotas. Atsakyk lietuviškai, vienu sakiniu, piktokai."
                )
                return response.text
            except Exception as e:
                self.logger.warning(f"Modelis {model_name} neveikia: {e}")
                continue # Jei metė 404, bando kitą sąraše
        
        return "DI SERVERIO TRIKDIS"
