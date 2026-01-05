import asyncio
import os
import RPi.GPIO as GPIO
import time
from PIL import Image
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- APARATŪROS KONFIGŪRACIJA ---
DC_GPIO  = 24  # Pin 18
RST_GPIO = 25  # Pin 22
CS_DEVICE = 0  # Pin 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicFinal:
    def __init__(self):
        self.display_active = False
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets")
        
        # 1. Fizinis RESET (Išvalome valdiklio atmintį)
        GPIO.setup(RST_GPIO, GPIO.OUT)
        GPIO.output(RST_GPIO, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST_GPIO, GPIO.HIGH)
        time.sleep(0.1)

        try:
            # 2. SPI inicializacija
            self.serial_spi = spi(port=0, device=CS_DEVICE, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO, baudrate=8000000)
            
            # 3. Įrenginio kūrimas su OFFSET pataisymais
            # Daugumai TZT 2.0" ekranų reikia y_offset=0 arba y_offset=80
            # Pradedame nuo 0, jei vaizdas vis tiek su juosta - bandysime 80
            self.device = st7789(
                self.serial_spi, 
                width=240, 
                height=320, 
                rotate=1, 
                x_offset=0, 
                y_offset=0
            )
            
            # Spalvų inversija (INVON)
            self.device.command(0x21) 
            
            self.display_active = True
            print("[OK] Ekranas inicijuotas su poslinkio kontrole.")
        except Exception as e:
            print(f"[KLAIDA] Ekranas: {e}")

        self.frames = []
        self._load_emotion("neutral")

    def _load_emotion(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            # Įsitikiname, kad vaizdas užpildo visą 320x240 plotą
            self.frames = [Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240)) for f in files]
            print(f"[OK] Užkrauta: {emotion}")
        except:
            # Jei neranda, sukuriam ryškų kadrą testui
            img = Image.new("RGB", (320, 240), (0, 255, 0)) # Žalia
            self.frames = [img]

    async def animation_loop(self):
        while self.display_active:
            current_set = list(self.frames)
            for frame in current_set:
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
