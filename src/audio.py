import sounddevice as sd
import vosk
import json
import logging
import asyncio
import os
import google.generativeai as genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self, model_path="/home/cm4/robot-project/src/model"):
        self.logger = logging.getLogger("AudioBrain")
        
        # 1. Gemini konfigūravimas (Saugus būdas)
        try:
            with open(os.path.join(BASE_DIR, "secrets.txt"), "r") as f:
                api_key = f.read().strip()
            genai.configure(api_key=api_key)
            self.ai_model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("Gemini API raktas užkrautas.")
        except:
            self.logger.error("API raktas nerastas faile secrets.txt!")
            self.ai_model = None

        # 2. Vosk (Raktažodis)
        try:
            self.model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
        except:
            self.logger.error("Vosk modelis nerastas.")
            self.recognizer = None

    async def monitor_wake_word(self):
        """Imituojame raktažodžio radimą kas 30 sekundžių (testui gynimui)"""
        while True:
            await asyncio.sleep(25)
            yield True

    async def record_audio(self, duration=3):
        self.logger.info("Klausausi...")
        await asyncio.sleep(duration)
        return "Simulated audio content"

    async def send_to_gemini_pro(self, audio_data):
        if not self.ai_model: return "No AI Model available."
        
        self.logger.info("Užklausa į Gemini...")
        prompt = "Tu esi Evil Sonic. Atsakyk trumpai ir grėsmingai lietuviškai."
        response = await asyncio.to_thread(self.ai_model.generate_content, prompt)
        return response.text
    except Exception as e:
        return f"KLAIDA: {e}"
