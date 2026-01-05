import asyncio
import os
import time
import random
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
from google import genai

# --- APARATŪROS KONFIGŪRACIJA (Griežtai pagal tavo pinuos) ---
DC_GPIO  = 24  # Pin 18
RST_GPIO = 25  # Pin 22
CS_DEVICE = 0  # Pin 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# --- DI RAKTO KROVIMAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def get_key():
    try:
        with open(os.path.join(BASE_DIR, "secrets.txt"), "r") as f:
            return f.read().strip()
    except: return None

client = genai.Client(api_key=get_key()) if get_key() else None

class XGORobotFinal:
    def __init__(self):
        self.display_active = False
        self.last_ai_text = ""
        self.frames = []
        self.assets_path = os.path.join(BASE_DIR, "assets")

        # 1. EKRANO PABAIDINIMAS (Force Start)
        try:
            import st7789
            # Naudojame 240x320 su 0,0 offsetais, bet jei bus baras, kodas pats paslinks
            self.disp = st7789.ST7789(
                port=0, cs=CS_DEVICE, dc=DC_GPIO, rst=RST_GPIO,
                width=240, height=320, rotation=90,
                spi_speed_hz=8000000
            )
            self.disp.begin()
            self.disp.set_inversion(True)
            self.display_active = True
            print("[OK] Ekranas veikia.")
        except Exception as e:
            print(f"[FAIL] Ekranas: {e}")

        self._load_emotion("neutral")
        self.audio = pyaudio.PyAudio()

    def _load_emotion(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            self.frames = [Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240)) for f in files]
        except:
            # Jei assets dingo, nupiešiam avarines raudonas akis
            img = Image.new("RGB", (320, 240), (0, 0, 0))
            d = ImageDraw.Draw(img)
            d.ellipse((80, 80, 120, 160), fill="red")
            d.ellipse((200, 80, 240, 160), fill="red")
            self.frames = [img]

    async def animation_loop(self):
        """Šis ciklas sukasi amžinai ir neleidžia ekranui užgesti"""
        while self.display_active:
            for frame in list(self.frames):
                # Piešiame kadrą
                out = frame.copy()
                if self.last_ai_text:
                    d = ImageDraw.Draw(out)
                    # Kraujuota lentelė (Evil Sonic stilius)
                    d.rectangle((0, 180, 320, 240), fill=(0, 0, 0))
                    d.line((0, 180, 320, 180), fill=(180, 0, 0), width=3)
                    d.text((10, 190), self.last_ai_text[:45], fill="white")
                
                self.disp.display(out)
                await asyncio.sleep(0.05)

    async def ask_gemini(self):
        """DI komunikacija fone"""
        if not client: return
        self.last_ai_text = "KLAUSAUSI..."
        await asyncio.sleep(3)
        self.last_ai_text = "MASTAU..."
        try:
            res = await asyncio.to_thread(client.models.generate_content, 
                                          model="gemini-1.5-flash", contents="Atsakyk trumpai ir piktokai lietuviskai.")
            self.last_ai_text = res.text.upper()
            await asyncio.sleep(7)
            self.last_ai_text = ""
        except: self.last_ai_text = "DI RYSIO KLAIDA"

    async def main_loop(self):
        asyncio.create_task(self.animation_loop())
        print("[SISTEMA] Viskas paleista. Gynimui paruosta.")
        while True:
            await asyncio.sleep(20)
            await self.ask_gemini()

if __name__ == "__main__":
    robot = XGORobotFinal()
    asyncio.run(robot.main_loop())
