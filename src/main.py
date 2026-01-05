import asyncio
import os
import RPi.GPIO as GPIO
import time
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- TAVO PATVIRTINTI PINAI (GPIO) ---
DC_GPIO  = 24  # Pin 18
RST_GPIO = 25  # Pin 22
CS_DEVICE = 0  # Pin 24 (CE0)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicFinal:
    def __init__(self):
        self.display_active = False
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets")
        
        # 1. Fizinis ekrano perkrovimas (kad dingtų sniegas)
        print("[*] Perkranu ekrano valdiklį...")
        GPIO.setup(RST_GPIO, GPIO.OUT)
        GPIO.output(RST_GPIO, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(RST_GPIO, GPIO.HIGH)
        time.sleep(0.2)

        try:
            # 2. SPI inicializacija (Lėtas greitis = nulis triukšmo)
            self.serial_spi = spi(port=0, device=CS_DEVICE, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO, baudrate=8000000)
            
            # 3. Įrenginio kūrimas (su TZT 2.0" specifika)
            self.device = st7789(self.serial_spi, width=240, height=320, rotation=1)
            self.device.set_inversion(True)
            self.display_active = True
            print("[OK] Ekranas paruoštas be triukšmo.")
        except Exception as e:
            print(f"[ERROR] Ekranas: {e}")

        self.frames = []
        self._load_emotion("neutral")

    def _load_emotion(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            self.frames = [Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240)) for f in files]
        except:
            # Jei neranda failų, nupiešia bent žalią kvadratą (testui)
            img = Image.new("RGB", (320, 240), (0, 255, 0))
            self.frames = [img]

    async def animation_loop(self):
        """Suka animaciją fone"""
        while self.display_active:
            for frame in self.frames:
                self.device.display(frame)
                await asyncio.sleep(0.05)

    async def main_loop(self):
        # Paleidžiame animaciją
        asyncio.create_task(self.animation_loop())
        print("[OK] Sistema veikia.")
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    robot = EvilSonicFinal()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
