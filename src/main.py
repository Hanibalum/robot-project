import time
import os
import RPi.GPIO as GPIO
from PIL import Image
import st7789 # Jei neturi, rasyk: pip install st7789

# --- TAVO FIZINIAI KONTAKTAI (PATIKRINTA) ---
# Pin 24 (CS) -> GPIO 8 (device 0)
# Pin 18 (DC) -> GPIO 24
# Pin 22 (RST) -> GPIO 25
DC_PIN  = 24
RST_PIN = 25
CS_PIN  = 0  # Spidev 0.0

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicRescue:
    def __init__(self):
        print("[*] PRADEDAMAS EKRANO ATGAIVINIMAS...")
        
        # 1. HARDWARE RESET (Fizinis perkrovimas)
        GPIO.setup(RST_PIN, GPIO.OUT)
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.2)

        try:
            # 2. Naudojame 320x240 rezoliuciją (gulsčią), kad nemestų klaidų
            self.disp = st7789.ST7789(
                port=0, 
                cs=CS_PIN, 
                dc=DC_PIN, 
                rst=RST_PIN, 
                width=320, 
                height=240, 
                rotation=90, 
                spi_speed_hz=8000000
            )
            self.disp.begin()
            print("[OK] Valdiklis priėmė komandas.")
        except Exception as e:
            print(f"[FAIL] Inicijavimas: {e}")

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets", "neutral")
        self.frames = []
        self._load_frames()

    def _load_frames(self):
        """Užkrauna bandomąjį vaizdą"""
        try:
            # Pirmiausia sukuriam RYŠKIAI BALTĄ kadrą (testui)
            test_img = Image.new("RGB", (320, 240), (255, 255, 255))
            self.frames.append(test_img)
            
            # Bandome užkrauti tavo nuotraukas
            if os.path.exists(self.assets_path):
                files = sorted([f for f in os.listdir(self.assets_path) if f.endswith('.png')])
                if files:
                    for f in files[:10]:
                        img = Image.open(os.path.join(self.assets_path, f)).convert("RGB").resize((320, 240))
                        self.frames.append(img)
                    print(f"[OK] Užkrauta kadrų: {len(self.frames)}")
        except:
            pass

    def run(self):
        print("[*] SIUNČIU VAIZDĄ Į EKRANĄ...")
        while True:
            for frame in self.frames:
                self.disp.display(frame)
                time.sleep(0.05)

if __name__ == "__main__":
    robot = EvilSonicRescue()
    robot.run()
