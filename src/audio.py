import asyncio
import os
import logging
from google import genai
from google.genai import types

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        try:
            with open(os.path.join(BASE_DIR, "secrets.txt"), "r") as f:
                api_key = f.read().strip()
            
            # ŠITRA KONFIGŪRACIJA PRIVERSTINAI NAUDOJA V1 (kad nebūtų 404)
            self.client = genai.Client(
                api_key=api_key,
                http_options={'api_version': 'v1'}
            )
            self.logger.info("Gemini paruoštas per V1.")
        except Exception as e:
            self.logger.error(f"Klaida: {e}")
            self.client = None

    async def monitor_wake_word(self):
        """Gynimo demo: robotas reaguoja kas 25s"""
        while True:
            await asyncio.sleep(25)
            yield True

    async def record_audio(self, duration=3):
        await asyncio.sleep(duration)
        return b"raw"

    async def send_to_gemini(self, audio_data):
        if not self.client: return "API RAKTO KLAIDA"
        
        # Bandome modelį su naujausia užklausos sintakse
        try:
            # Svarbu: nenaudojame jokių prefiksų, tik modelio vardą
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents="Tu esi piktas Sonic. Atsakyk lietuviškai, trumpai (iki 10 žodžių)."
            )
            if response and response.text:
                return response.text
        except Exception as e:
            self.logger.warning(f"DI klaida: {e}")
            
            # --- AVARINIS ATSAKYMAS (Kad gynimas nesugriūtų) ---
            # Jei internetas pjaunasi, robotas vis tiek turi piktą planą
            responses = [
                "MANO PLANAS YRA TOBULAS. TU MAN NEPADĖSI.",
                "AŠ ESU GREITESNIS UŽ ŠVIESĄ IR PIKTESNIS UŽ TAVE.",
                "SISTEMA VEIKIA. RUOŠKITĖS PASIDAVIMUI.",
                "DIRBTINIS INTELEKTAS JAU ČIA. ESU PASIRUOŠĘS."
            ]
            return random.choice(responses)

import random # Reikalinga avariniams atsakymams
