import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
import time
import random
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- NAUJAS GOOGLE DI ---
from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_api_key():
    try:
        with open(os.path.join(BASE_DIR, "secrets.txt"), "r") as f:
            return f.read().strip()
    except: return None

API_KEY = load_api_key()
client = genai.Client(api_key=API_KEY) if API_KEY else None

# Ekrano konfigūracija
DC_GPIO, RST_GPIO, CS_ID = 24, 25, 0
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicRobot:
    def __init__(self):
        try:
            serial_spi = spi(port=0, device=CS_ID, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO)
            self.device = st7789(serial_spi, width=240, height=320, rotation=1)
            self.device.set_inversion(True)
            self.display_active = True
        except: self.display_active = False

        self.assets_path = os.path.join(BASE_DIR, "assets")
        self.frames = []
        self.last_ai_text = ""
        self._load_emotion("neutral")
        self.audio = pyaudio.PyAudio()

    def _load_emotion(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            self.frames = [Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240)) for f in files]
        except:
            img = Image.new("RGB", (320, 240), "black")
            draw = ImageDraw.Draw(img)
            draw.ellipse((80, 80, 120, 160), fill="red")
            draw.ellipse((200, 80, 240, 160), fill="red")
            self.frames = [img]

    async def animation_loop(self):
        """Šis ciklas NIEKADA neturi sustoti"""
        print("[*] Animacija pradedama...")
        while self.display_active:
            current_set = list(self.frames) # Kopija saugumui
            for frame in current_set:
                if self.last_ai_text:
                    canvas = frame.copy()
                    draw = ImageDraw.Draw(canvas)
                    draw.rectangle((0, 170, 320, 240), fill=(0, 0, 0))
                    draw.line((0, 170, 320, 170), fill=(200, 0, 0), width=3)
                    draw.text((10, 185), self.last_ai_text[:45], fill="white")
                    self.device.display(canvas)
                else:
                    self.device.display(frame)
                await asyncio.sleep(0.05)

    async def ask_gemini(self, question):
        if not client: 
            self.last_ai_text = "API RAKTO KLAIDA"
            return
        
        self.last_ai_text = "MASTAU..."
        try:
            # Naujas Gemini API kvietimo būdas
            prompt = f"Tu esi Evil Sonic. Atsakyk lietuviškai, trumpai ir grėsmingai: {question}"
            response = await asyncio.to_thread(
                client.models.generate_content, 
                model="gemini-1.5-flash", 
                contents=prompt
            )
            self.last_ai_text = response.text.upper()
            await asyncio.sleep(8)
            self.last_ai_text = ""
        except Exception as e:
            print(f"DI Klaida: {e}")
            self.last_ai_text = "DI RYSIO KLAIDA"

    async def main_loop(self):
        # Paleidžiame vaizdą
        asyncio.create_task(self.animation_loop())
        print("[OK] Sistema paruošta.")
        
        while True:
            # Čia bus balso įrašymas, dabar - ciklas
            await asyncio.sleep(30)
            await self.ask_gemini("Koks tavo planas?")

if __name__ == "__main__":
    robot = EvilSonicRobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()



