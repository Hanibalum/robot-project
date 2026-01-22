import asyncio
import os
import google.generativeai as genai

class AudioBrain:
    def __init__(self):
        try:
            with open('/home/cm4/robot-project/src/secrets.txt', 'r') as f:
                api_key = f.read().strip()
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("[OK] Gemini paruoštas stabiliai.")
        except:
            self.model = None

    async def monitor_wake_word(self):
        while True:
            await asyncio.sleep(20)
            yield True

    async def record_audio(self, duration=3):
        await asyncio.sleep(duration)
        return "data"

    async def send_to_gemini(self, audio_data):
        if not self.model: return "API RAKTO KLAIDA"
        try:
            # Senuoju, stabiliu būdu
            response = await asyncio.to_thread(self.model.generate_content, "Atsakyk lietuviškai, trumpai, piktokai.")
            return response.text
        except Exception as e:
            return f"DI TRIKDIS: {str(e)[:40]}"
