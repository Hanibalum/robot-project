import asyncio
import os
import time
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- TAVO PATVIRTINTI KONTAKTAI (GPIO numeriai) ---
# Pin 18 (DC) -> GPIO 24
# Pin 22 (RST) -> GPIO 25
# Pin 24 (CS) -> GPIO 8 (device 0)
DC_GPIO  = 24  
RST_GPIO = 25  
CS_DEVICE = 0  

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class XGORobotRescue:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets")
        self.display_active = False

        # 1. HARDWARE RESET
        print("[*] Vykdomas aparatūrinis RESET...")
        GPIO.setup(RST_GPIO, GPIO.OUT)
        GPIO.output(RST_GPIO, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(RST_GPIO, GPIO.HIGH)
        time.sleep(0.2)

        try:
            # 2. Inicijuojame SPI (port=0, device=0 yra Pin 24)
            # baudrate 8MHz yra saugiausias
            self.serial = spi(port=0, device=CS_DEVICE, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO, baudrate=8000000)
            
            # 3. Inicijuojame įrenginį STANDARTINIU režimu (be rotacijos, kad nekiltų klaidų)
            self.device = st7789(self.serial, width=240, height=320, rotate=0)
            
            # 4. TIESIOGINĖ KOMANDA INVERSIJAI (Pažadina TZT ekranus)
            self.device.command(0x21) 
            
            self.display_active = True
            print("[OK] Ekranas sukonfigūruotas.")
        except Exception as e:
            print(f"[FAIL] Ekranas: {e}")

        self.frames = []
        self._load_and_rotate_frames("neutral")

    def _load_and_rotate_frames(self, emotion):
        """Užkrauna ir pasuka nuotraukas rankiniu būdu, kad biblioteka ne rėktų"""
        path = os.path.join(self.assets_path, emotion)
        self.frames = []
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            if not files: raise Exception("Nėra failų")
            for f in files[:20]:
                img = Image.open(os.path.join(path, f)).convert("RGB")
                # Padarom gulsčią (320x240) ir tada pasukam į (240x320)
                img = img.resize((320, 240))
                img = img.rotate(90, expand=True)
                self.frames.append(img)
            print(f"[OK] Užkrauta {len(self.frames)} kadrų.")
        except Exception as e:
            print(f"[WARN] Emocijų klaida: {e}")
            # AVARINIS VAIZDAS (Mėlynas kvadratas per visą ekraną)
            img = Image.new("RGB", (240, 320), (0, 0, 255))
            self.frames = [img]

    async def animation_loop(self):
        print("[*] Animacija paleista.")
        while self.display_active:
            for frame in self.frames:
                self.device.display(frame)
                await asyncio.sleep(0.05)

    async def main_loop(self):
        # Paleidžiame tik vaizdą
        asyncio.create_task(self.animation_loop())
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    robot = XGORobotRescue()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
