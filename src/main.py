import asyncio
import os
import time
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import st7789

# --- KONTAKTAI ---
DC_GPIO  = 24  # Pin 18
RST_GPIO = 25  # Pin 22
CS_DEVICE = 0  # Pin 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicGynimas:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets", "neutral")
        self.display_active = False
        
        # 1. HARDWARE RESET
        GPIO.setup(RST_GPIO, GPIO.OUT)
        GPIO.output(RST_GPIO, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(RST_GPIO, GPIO.HIGH)
        time.sleep(0.2)

        try:
            # KONFIGŪRACIJA: TZT 2.0" ekranams dažnai padeda 240x240 nustatymas 
            # net jei ekranas yra 240x320 - tai panaikina triukšmą šone.
            self.disp = st7789.ST7789(
                port=0, cs=CS_DEVICE, dc=DC_GPIO, rst=RST_GPIO,
                width=240, height=320, rotation=0, 
                spi_speed_hz=4000000 # Mažas greitis užtikrina švarų vaizdą
            )
            self.disp.begin()
            self.disp.set_inversion(True)
            self.display_active = True
            print("[OK] Ekranas paleistas. Valau triukšmą...")
        except Exception as e:
            print(f"[FAIL] {e}")

        self.frames = []
        self._load_and_prepare_frames()

    def _load_and_prepare_frames(self):
        """Užkrauna ir pasuka nuotraukas taip, kad jos uždengtų sniegą"""
        try:
            if not os.path.exists(self.assets_path): raise Exception("Nėra assets")
            files = sorted([f for f in os.listdir(self.assets_path) if f.endswith('.png')])
            
            for f in files[:20]:
                img = Image.open(os.path.join(self.assets_path, f)).convert("RGB")
                # DAROME TRIPLE-FIX:
                # 1. Rezaisinam į tikslų ekrano dydį
                # 2. Pasukame 90 laipsnių
                # 3. Išplečiame, kad uždengtų kraštus
                img = img.resize((320, 240)) 
                img = img.rotate(90, expand=True)
                self.frames.append(img)
            print(f"[OK] Paruošta kadrų: {len(self.frames)}")
        except:
            # Jei assets nėra, piešiam pilną juodą kadrą su raudonom akim
            img = Image.new("RGB", (240, 320), (0, 0, 0))
            d = ImageDraw.Draw(img)
            d.ellipse((40, 80, 100, 140), fill=(255, 0, 0))
            d.ellipse((140, 80, 200, 140), fill=(255, 0, 0))
            self.frames = [img]

    async def run(self):
        if not self.display_active: return
        while True:
            for frame in self.frames:
                # Siunčiame vaizdą. 
                # TZT ekranai dažnai turi 35-80 pikselių "negyvą" zoną RAM atmintyje.
                self.disp.display(frame)
                await asyncio.sleep(0.05)

if __name__ == "__main__":
    robot = EvilSonicGynimas()
    try:
        asyncio.run(robot.run())
    except KeyboardInterrupt:
        GPIO.cleanup()
