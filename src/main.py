import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
import st7789
import google.generativeai as genai
from PIL import Image, ImageDraw

# --- KONFIGŪRACIJA ---
# Įklijuok savo raktą čia:
genai.configure(api_key="TAVO_API_RAKTAS_CIA")
model = genai.GenerativeModel('gemini-1.5-flash')

# Ekrano Pinai (Pin -> GPIO)
# CS:Pin24(GPIO8), DC:Pin18(GPIO24), RST:Pin22(GPIO25)
DC_GPIO, RST_GPIO, CS_ID = 24, 25, 0

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicRobot:
    def __init__(self):
        # 1. Ekranas
        try:
            from luma.core.interface.serial import spi
            from luma.lcd.device import st7789 as st7789_luma
            serial_spi = spi(port=0, device=CS_ID, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO)
            self.device = st7789_luma(serial_spi, width=240, height=320, rotation=1)
            self.device.set_inversion(True)
            self.display_active = True
            print("[OK] Ekranas paruoštas.")
        except:
            self.display_active = False

        # 2. Emocijos
        self.assets_path = os.path.expanduser("~/robot-project/src/assets")
        self.current_emotion = "neutral"
        self.frames = []
        self.last_ai_text = ""
        self._load_emotion("neutral")

        # 3. Audio/UART
        self.audio = pyaudio.PyAudio()
        self.mic_index = 0
        self.uart_writer = None

    def _load_emotion(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            self.frames = [Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240)) for f in files]
            self.current_emotion = emotion
        except:
            # Jei neranda Emo Pet failų, sukuriam raudonas Evil Sonic akis
            img = Image.new("RGB", (320, 240), "black")
            draw = ImageDraw.Draw(img)
            draw.ellipse((80, 80, 120, 160), fill="red")
            draw.ellipse((200, 80, 240, 160), fill="red")
            self.frames = [img]

    async def animation_loop(self):
        while self.display_active:
            current_set = self.frames
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
                await asyncio.sleep(0.06)

    async def ask_gemini(self, question):
        self.last_ai_text = "MASTAU..."
        try:
            prompt = f"Tu esi Evil Sonic. Atsakyk labai trumpai ir piktai: {question}"
            response = await asyncio.to_thread(model.generate_content, prompt)
            self.last_ai_text = response.text.upper()
            await asyncio.sleep(8)
            self.last_ai_text = ""
        except:
            self.last_ai_text = "DI KLAIDA"

    async def uart_task(self):
        try:
            reader, writer = await serial_asyncio.open_serial_connection(url='/dev/serial0', baudrate=115200)
            self.uart_writer = writer
            while True:
                self.uart_writer.write(b'\x00')
                await self.uart_writer.drain()
                await asyncio.sleep(5)
        except: print("UART klaida")

    async def main_loop(self):
        asyncio.create_task(self.animation_loop())
        asyncio.create_task(self.uart_task())
        while True:
            await asyncio.sleep(25)
            await self.ask_gemini("What are you thinking?")

if __name__ == "__main__":
    robot = EvilSonicRobot()
    asyncio.run(robot.main_loop())

