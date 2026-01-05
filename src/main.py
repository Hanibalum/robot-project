import time
import os
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import st7789

# --- TAVO KONTAKTAI (Pin -> GPIO) ---
# Pin 24 (CS) -> GPIO 8 (device 0)
# Pin 18 (DC) -> GPIO 24
# Pin 22 (RST) -> GPIO 25
DC_PIN  = 24
RST_PIN = 25
CS_PIN  = 0  

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicGynimas:
    def __init__(self):
        print("[*] EKRANO KONFIGŪRAVIMAS...")
        
        # 1. Fizinis RESET
        GPIO.setup(RST_PIN, GPIO.OUT)
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST_GPIO if 'RST_GPIO' in locals() else RST_PIN, GPIO.HIGH)
        time.sleep(0.1)

        # 2. Inicijavimas (Griežtai be rotacijos dravierio lygmenyje)
        self.disp = st7789.ST7789(
            port=0, 
            cs=CS_PIN, 
            dc=DC_PIN, 
            rst=RST_PIN,
            width=240, 
            height=320, 
            rotation=0, # 0, kad nekiltų klaidos
            spi_speed_hz=8000000
        )
        self.disp.begin()
        
        # TZT ekranams dažnai reikia šito:
        try:
            self.disp.set_inversion(True)
        except:
            self.disp.command(0x21) # Tiesioginis INVON

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets", "neutral")
        self.frames = []
        self._load_and_rotate_frames()

    def _load_and_rotate_frames(self):
        """Paruošiame vaizdą: gulsčią 320x240 paverčiame į stovintį 240x320"""
        try:
            if os.path.exists(self.assets_path):
                files = sorted([f for f in os.listdir(self.assets_path) if f.endswith('.png')])
                for f in files[:20]:
                    img = Image.open(os.path.join(self.assets_path, f)).convert("RGB")
                    # Pasukame rankiniu būdu 90 laipsnių
                    img = img.resize((320, 240))
                    img = img.rotate(90, expand=True)
                    self.frames.append(img)
                print(f"[OK] Užkrauta kadrų: {len(self.frames)}")
            
            if not self.frames:
                # Jei nėra failų - ryškiai BALTAS ekranas testui
                print("[WARN] Assets nerasti, piešiu bandomąjį kadrą.")
                test_img = Image.new("RGB", (240, 320), (255, 255, 255))
                self.frames = [test_img]
        except Exception as e:
            print(f"Klaida ruošiant vaizdus: {e}")

    def run(self):
        print("[OK] PRADEDAMAS IŠVEDIMAS Į EKRANĄ.")
        while True:
            for frame in self.frames:
                self.disp.display(frame)
                time.sleep(0.05)

if __name__ == "__main__":
    try:
        robot = EvilSonicGynimas()
        robot.run()
    except KeyboardInterrupt:
        GPIO.cleanup()
