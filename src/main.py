import asyncio
import os
import time
import RPi.GPIO as GPIO
from PIL import Image
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- KONTAKTAI ---
DC_GPIO  = 24  
RST_GPIO = 25  
CS_DEVICE = 0  

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicFinal:
    def __init__(self):
        self.display_active = False
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets")
        
        # 1. HARDWARE RESET
        GPIO.setup(RST_GPIO, GPIO.OUT)
        GPIO.output(RST_GPIO, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST_GPIO, GPIO.HIGH)
        time.sleep(0.1)

        try:
            # SPI inicializacija
            self.serial = spi(port=0, device=CS_DEVICE, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO, baudrate=8000000)
            
            # --- POSLINKIO (OFFSET) KEITIMAS ---
            # Jei vaizdas vis tiek su juosta, po paleidimo pakeisime x_offset į 0, o y_offset į 35
            self.device = st7789(
                self.serial, 
                width=240, 
                height=320, 
                rotate=0, 
                x_offset=35, # BANDOME ŠITĄ (Horizontalus poslinkis)
                y_offset=0
            )
            
            self.device.command(0x21) # Inversija spalvoms
            self.display_active = True
            print("[OK] Ekranas inicijuotas. Ar dingo sniegas?")
        except Exception as e:
            print(f"[FAIL] Ekranas: {e}")

        self.frames = []
        self._load_and_rotate_frames("neutral")

    def _load_and_rotate_frames(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        self.frames = []
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            for f in files[:30]:
                img = Image.open(os.path.join(path, f)).convert("RGB")
                img = img.resize((320, 240))
                img = img.rotate(90, expand=True)
                self.frames.append(img)
            print(f"[OK] Užkrauta: {emotion}")
        except:
            # Jei assets neranda, nupiešiam avarines akis
            img = Image.new("RGB", (240, 320), (0, 0, 0))
            from PIL import ImageDraw
            d = ImageDraw.Draw(img)
            d.ellipse((40, 60, 100, 180), fill=(255, 0, 0))
            d.ellipse((140, 60, 200, 180), fill=(255, 0, 0))
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
