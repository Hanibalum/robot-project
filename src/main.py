import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
import random
import st7789
import google.generativeai as genai
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789 as st7789_luma

# --- KONFIGŪRACIJA ---
API_KEY = "TAVO_API_RAKTAS_CIA" # Įklijuok savo Gemini raktą
genai.configure(api_key=API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# Ekrano Pinai (pagal tavo schemą)
DC_GPIO, RST_GPIO, CS_ID = 24, 25, 0
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class EvilSonicRobot:
    def __init__(self):
        # 1. Ekranas (Luma.lcd)
        try:
            # Pin 18 (Backlight) perkeltas į 3.3V fiziškai, todėl čia jo nebevaldom
            serial_spi = spi(port=0, device=CS_ID, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO)
            self.device = st7789_luma(serial_spi, width=240, height=320, rotation=1)
            self.device.set_inversion(True)
            self.display_active = True
        except Exception as e:
            print(f"Ekrano klaida: {e}")
            self.display_active = False

        # 2. Emocijų valdiklis
        self.assets_path = "src/assets" # Čia turi būti aplankai: neutral, happy ir t.t.
        self.current_emotion = "neutral"
        self.frames = []
        self.last_ai_text = ""
        self._load_emotion("neutral")

        # 3. Audio (ICS-43434)
        self.audio = pyaudio.PyAudio()
        self.mic_index = 0

    def _load_emotion(self, emotion):
        """Užkrauna animacijos kadrus iš atitinkamo aplanko"""
        path = os.path.join(self.assets_path, emotion)
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            self.frames = [Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240)) for f in files]
            self.current_emotion = emotion
        except:
            print(f"Klaida kraunant {emotion}. Naudojamas neutral.")
            # Jei neranda, bandom bent neutral užkrauti
            if emotion != "neutral": self._load_emotion("neutral")

    async def animation_loop(self):
        """Aukšto prioriteto gija: nuolatinis kadrų piešimas"""
        print("[*] HMI: Animacijos ciklas aktyvus.")
        while self.display_active:
            # Dirbame su kopija, kad išvengtume klaidų kai keičiasi emocija
            current_frames = self.frames 
            for frame in current_frames:
                # Jei turime DI atsakymą, uždedame jį ant akių
                if self.last_ai_text:
                    canvas = frame.copy()
                    draw = ImageDraw.Draw(canvas)
                    # Kraujuota Evil Sonic lentelė apačioje
                    draw.rectangle((0, 180, 320, 240), fill=(0, 0, 0))
                    draw.line((0, 180, 320, 180), fill=(200, 0, 0), width=2)
                    draw.text((10, 190), self.last_ai_text[:40], fill="white")
                    self.device.display(canvas)
                else:
                    self.device.display(frame)
                await asyncio.sleep(0.06)

    async def ai_process(self, user_input):
        """DI procesas: Gemini užklausa ir emocijos parinkimas"""
        try:
            self.last_ai_text = "MASTAU..."
            prompt = f"Tu esi Evil Sonic. Atsakyk trumpai, grėsmingai. Vartotojas klausia: {user_input}. " \
                     f"Atsakymo pabaigoje pridėk nuotaiką: [happy, sad, angry, neutral]."
            
            response = await asyncio.to_thread(ai_model.generate_content, prompt)
            raw_text = response.text.lower()
            
            # Atskiriame tekstą nuo emocijos
            if "happy" in raw_text: self._load_emotion("happy")
            elif "sad" in raw_text: self._load_emotion("sad")
            elif "angry" in raw_text: self._load_emotion("angry")
            else: self._load_emotion("neutral")
            
            self.last_ai_text = response.text.split('[')[0].strip().upper()
            await asyncio.sleep(6) # Rodome atsakymą 6 sek.
            self.last_ai_text = ""
        except:
            self.last_ai_text = "DI RYSIO KLAIDA"

    async def main_loop(self):
        # Paleidžiame animaciją
        asyncio.create_task(self.animation_loop())
        
        while True:
            # Čia ateityje bus tavo balso klausymas (Speech-to-Text)
            # Dabar imituojame klausimą kas 30 sekundžių
            await asyncio.sleep(30)
            await self.ai_process("Koks tavo planas?")

if __name__ == "__main__":
    robot = EvilSonicRobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
