import asyncio
import os
import time
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import st7789

# --- TAVO FIZINIAI KONTAKTAI ---
DC_GPIO  = 24  # Pin 18
RST_GPIO = 25  # Pin 22
CS_DEVICE = 0  # Pin 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicGynimas:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets", "neutral")
        
        # 1. HARDWARE RESET
        GPIO.setup(RST_GPIO, GPIO.OUT)
        GPIO.output(RST_GPIO, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(RST_GPIO, GPIO.HIGH)
        time.sleep(0.2)

        try:
            # TZT 2.0" modulio specifika (240x320 valdiklis, bet 240x240 arba 240x320 stiklas)
            # Pridedame x_offset ir y_offset, kad "pagautume" vaizdą
            self.disp = st7789.ST7789(
                port=0, cs=CS_DEVICE, dc=DC_GPIO, rst=RST_GPIO,
                width=240, height=320, rotation=0, 
                x_offset=0, y_offset=0, # Pradedame nuo 0
                spi_speed_hz=8000000
            )
            self.disp.begin()
            self.disp.set_inversion(True) # SVARBU: TZT be šito rodys juodai
            self.display_active = True
            print("[OK] Ekranas paleistas. Siunčiu bandomąjį vaizdą...")
        except Exception as e:
            print(f"[FAIL] {e}")
            self.display_active = False

        self.frames = []
        self._load_and_prepare_frames()

    def _load_and_prepare_frames(self):
        """Užkrauna, rezaisina ir pasuka nuotraukas rankiniu būdu"""
        try:
            # Jei tavo assets aplanke yra failų, juos surikiuojam
            files = [f for f in os.listdir(self.assets_path) if f.endswith('.png')]
            if not files: raise Exception("Nėra PNG failų")
            
            for f in sorted(files)[:10]: # Imam pirmus 10 kadrų greičiui
                img = Image.open(os.path.join(self.assets_path, f)).convert("RGB")
                # Sukeičiam proporcijas, nes suksim 90 laipsnių
                img = img.resize((320, 240)) 
                img = img.rotate(90, expand=True)
                self.frames.append(img)
            print(f"[OK] Paruošta kadrų: {len(self.frames)}")
        except Exception as e:
            print(f"[WARN] Assets klaida ({e}). Naudoju avarinį vaizdą.")
            # AVARINIS VAIZDAS: Ryškiai raudona spalva, kad matytume, jog ekranas gyvas
            img = Image.new("RGB", (240, 320), (255, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rectangle((20, 20, 220, 300), outline="white", fill="red")
            self.frames = [img]

    async def run(self):
        if not self.display_active: return
        
        while True:
            for frame in self.frames:
                self.disp.display(frame)
                await asyncio.sleep(0.05)

if __name__ == "__main__":
    robot = EvilSonicGynimas()
    try:
        asyncio.run(robot.run())
    except KeyboardInterrupt:
        GPIO.cleanup()
