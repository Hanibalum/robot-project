iimport asyncio
import os
import RPi.GPIO as GPIO
import time
from PIL import Image
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- APARATŪRA ---
DC_GPIO, RST_GPIO, CS_DEVICE = 24, 25, 0
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicFinal:
    def __init__(self):
        self.display_active = False
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets")
        
        # Fizinis RESET
        GPIO.setup(RST_GPIO, GPIO.OUT)
        GPIO.output(RST_GPIO, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST_GPIO, GPIO.HIGH)
        time.sleep(0.1)

        try:
            self.serial_spi = spi(port=0, device=CS_DEVICE, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO, baudrate=8000000)
            
            # --- POSLINKIO (OFFSET) PATAISYMAS ---
            # Jei juosta vis dar bus, čia keisime y_offset reikšmę
            self.device = st7789(
                self.serial_spi, 
                width=240, 
                height=320, 
                rotate=1, 
                x_offset=0, 
                y_offset=0 # Pradedam nuo 0, bet žemiau nurodysiu ką daryti jei nepadės
            )
            
            self.device.command(0x21) # Inversija
            self.display_active = True
            print("[OK] Ekranas inicijuotas. Tikriname poslinkį...")
        except Exception as e:
            print(f"[KLAIDA] {e}")

        self.frames = []
        self._load_emotion("neutral")

    def _load_emotion(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            self.frames = [Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240)) for f in files]
        except:
            # Jei nėra emocijų, nuspalvinam ekraną pilnai, kad matytume ar juosta dingo
            img = Image.new("RGB", (320, 240), (255, 0, 0)) # Raudona
            self.frames = [img]

    async def animation_loop(self):
        while self.display_active:
            for frame in self.frames:
                self.device.display(frame)
                await asyncio.sleep(0.05)

    async def main_loop(self):
        asyncio.create_task(self.animation_loop())
        while True: await asyncio.sleep(1)

if __name__ == "__main__":
    robot = EvilSonicFinal()
    try: asyncio.run(robot.main_loop())
    except KeyboardInterrupt: GPIO.cleanup()
