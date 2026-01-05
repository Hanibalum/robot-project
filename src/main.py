import asyncio
import os
import time
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import st7789

# --- KONTAKTAI (GPIO) ---
DC_GPIO  = 24  # Pin 18
RST_GPIO = 25  # Pin 22
CS_DEVICE = 0  # Pin 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicRescue:
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
            # Paprasčiausia iniciacija be jokių offsetų, kad nemestų klaidų
            self.disp = st7789.ST7789(
                port=0, 
                cs=CS_DEVICE, 
                dc=DC_GPIO, 
                rst=RST_GPIO,
                width=240, 
                height=320, 
                rotation=90, 
                spi_speed_hz=8000000
            )
            self.disp.begin()
            
            # IŠBANDOME ABI INVERSIJOS BŪSENAS
            self.disp.set_inversion(True) 
            
            self.display_active = True
            print("[OK] Ekranas paleistas. Siunčiu BALTĄ testą...")
        except Exception as e:
            print(f"[FAIL] Ekranas: {e}")
            self.display_active = False

        self.frames = []
        self._load_frames()

    def _load_frames(self):
        try:
            # Sukuriame ryškų testinį vaizdą (BALTĄ), kad pamatytume ar ekranas veikia
            test_img = Image.new("RGB", (320, 240), (255, 255, 255))
            draw = ImageDraw.Draw(test_img)
            draw.text((100, 110), "TESTAS: VEIKIA", fill=(255, 0, 0))
            
            # Bandome užkrauti tavo akis
            if os.path.exists(self.assets_path):
                files = sorted([f for f in os.listdir(self.assets_path) if f.endswith('.png')])
                if files:
                    for f in files[:15]:
                        img = Image.open(os.path.join(self.assets_path, f)).convert("RGB")
                        img = img.resize((320, 240))
                        self.frames.append(img)
                    print(f"[OK] Užkrauta kadrų: {len(self.frames)}")
            
            if not self.frames:
                self.frames = [test_img]
        except Exception as e:
            print(f"Klaida: {e}")
            self.frames = [Image.new("RGB", (320, 240), (255, 255, 255))]

    async def run(self):
        if not self.display_active: return
        print("[*] Pradedamas vaizdo rodymas...")
        while True:
            for frame in self.frames:
                self.disp.display(frame)
                await asyncio.sleep(0.05)

if __name__ == "__main__":
    robot = EvilSonicRescue()
    try:
        asyncio.run(robot.run())
    except KeyboardInterrupt:
        GPIO.cleanup()

