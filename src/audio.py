import asyncio
import os
import logging
import google.generativeai as genai

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        try:
            with open('/home/cm4/robot-project/src/secrets.txt', 'r') as f:
                api_key = f.read().strip()
            genai.configure(api_key=api_key)
            
            # DIAGNOSTIKA: Surandame, kokį modelį Google mums leidžia naudoti
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Prioritetas: 1.5-flash, tada pro, tada bet koks pirmas veikiantis
            if 'models/gemini-1.5-flash' in available_models:
                self.model_name = 'gemini-1.5-flash'
            elif 'models/gemini-pro' in available_models:
                self.model_name = 'gemini-pro'
            else:
                self.model_name = available_models[0].replace('models/', '')
            
            self.model = genai.GenerativeModel(self.model_name)
            self.logger.info(f"[OK] Naudojamas DI modelis: {self.model_name}")
        except Exception as e:
            self.logger.error(f"DI krovimo klaida: {e}")
            self.model = None

    async def monitor_wake_word(self):
        while True:
            await asyncio.sleep(20)
            yield True

    async def record_audio(self, duration=3):
        await asyncio.sleep(duration)
        return "data"

    async def send_to_gemini(self, audio_data):
        if not self.model: return "DI NEPASIEKIAMAS"
        try:
            # Trumpas, grėsmingas Evil Sonic atsakymas
            response = await asyncio.to_thread(self.model.generate_content, "Atsakyk kaip piktas robotas, labai trumpai lietuviškai.")
            return response.text
        except Exception as e:
            return f"RYŠIO KLAIDA: {str(e)[:30]}"
