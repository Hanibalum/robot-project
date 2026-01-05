import asyncio
import os
import time
import RPi.GPIO as GPIO
from PIL import Image
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- APARATŪRA ---
DC_GPIO  = 24  
RST_GPIO = 25  
CS_DEVICE = 0  

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicFinal:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets")
        self.display_active = False

        # 1. HARDWARE RESET
        GPIO.setup(RST_GPIO, GPIO.OUT)
        GPIO.output(RST_GPIO, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST_GPIO, GPIO.HIGH)
        time.sleep(0.1)

        try:
            self.serial = spi(port=0, device=CS_DEVICE, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO, baudrate=8000000)
            
            # --- POSLINKIO PATAISYMAS (OFFSET) ---
            # TZT 2.0" ekranams dažniausiai reikia y_offset=35 arba 0
            # Jei juosta nedings, pakeisime tik šitą skaičių
            self.device = st7789(
                self.serial, 
                width=240, 
                height=320, 
                rotate=0, 
                x_offset=0, 
                y_offset=35  # Šitas skaičius panaikina tavo "sniegą"
            )
            
            self.device.command(0x21) # Inversija spalvoms
            self.display_active = True
            print("[OK] Ekranas sukonfigūruotas su poslinkiu.")
        except Exception as e:
            print(f"[FAIL] Ekranas: {e}")

        self.frames = []
        self._load_and_rotate_frames("neutral")

    def _load_and_rotate_frames(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        self.frames = []
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            if not files: raise Exception("Nėra failų")
            for f in files[:30]: # Imam kadrus
                img = Image.open(os.path.join(path, f)).convert("RGB")
                img = img.resize((320, 240))
                img = img.rotate(90, expand=True) # Rankinis pasukimas
                self.frames.append(img)
            print(f"[OK] Užkrauta: {emotion}")
        except:
            # Jei assets neranda, piešiam avarines akis per visą ekraną
            img = Image.new("RGB", (240, 320), (0, 0, 0))
            from PIL import ImageDraw
            d = ImageDraw.Draw(img)
            d.ellipse((40, 60, 100, 180), fill=(255, 0, 0)) # Akis 1
            d.ellipse((140, 60, 200, 180), fill=(255, 0, 0)) # Akis 2
            self.frames = [img]

    async def animation_loop(self):
        while self.display_active:
            for frame in list(self.frames):
                self.device.display(frame)
                await asyncio.sleep(0.05)

    async def main_loop(self):
        asyncio.create_task(self.animation_loop())
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    robot = EvilSonicFinal()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
