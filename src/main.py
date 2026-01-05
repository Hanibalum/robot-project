import asyncio
import os
import time
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import st7789

# --- TAVO PINAI (FIZINIAI KONTAKTAI) ---
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
        time.sleep(0.1)
        GPIO.output(RST_GPIO, GPIO.HIGH)
        time.sleep(0.1)

        try:
            # KONFIGŪRACIJA BE ROTACIJOS (kad nebūtų klaidų)
            self.disp = st7789.ST7789(
                port=0, cs=CS_DEVICE, dc=DC_GPIO, rst=RST_GPIO,
                width=240, height=320, rotation=0, # Paliekam 0!
                spi_speed_hz=8000000
            )
            self.disp.begin()
            self.disp.set_inversion(True) 
            self.display_active = True
            print("[OK] Ekranas inicijuotas sėkmingai.")
        except Exception as e:
            print(f"[FAIL] Ekranas: {e}")

        self.frames = []
        self._load_and_rotate_frames()

    def _load_and_rotate_frames(self):
        """Užkrauna akis ir jas pasuka 90 laipsnių programiškai"""
        try:
            if not os.path.exists(self.assets_path):
                raise Exception("Assets nerasti")
            
            files = sorted([f for f in os.listdir(self.assets_path) if f.endswith('.png')])
            for f in files[:20]: # Imam pirmus 20 kadrų
                img = Image.open(os.path.join(self.assets_path, f)).convert("RGB")
                # Sukeičiam dydį: nuotrauka 320x240 tampa 240x320 po pasukimo
                img = img.resize((320, 240)) 
                img = img.rotate(90, expand=True) 
                self.frames.append(img)
            print(f"[OK] Paruošta {len(self.frames)} kadrų.")
        except Exception as e:
            print(f"[WARN] Klaida: {e}. Piešiu testinį vaizdą.")
            # AVARINIS VAIZDAS (Mėlynas kvadratas)
            img = Image.new("RGB", (320, 240), (0, 0, 255))
            img = img.rotate(90, expand=True)
            self.frames = [img]

    async def run_display(self):
        if not self.display_active: return
        print("[*] Rodau animaciją...")
        while True:
            for frame in self.frames:
                self.disp.display(frame)
                await asyncio.sleep(0.05)

if __name__ == "__main__":
    robot = EvilSonicGynimas()
    try:
        asyncio.run(robot.run_display())
    except KeyboardInterrupt:
        GPIO.cleanup()
