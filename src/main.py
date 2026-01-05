import time
import os
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import st7789

# --- KONTAKTAI (Griežtai pagal tavo sujungimą) ---
DC_PIN  = 24  # Pin 18
RST_PIN = 25  # Pin 22
CS_PIN  = 0   # Pin 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicGynimas:
    def __init__(self):
        print("[*] EKRANO ATGAIVINIMAS: AGRESYVUS REŽIMAS")
        
        # 1. Fizinis RESET (Išvalome šiukšles)
        GPIO.setup(RST_PIN, GPIO.OUT)
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.1)

        try:
            # 2. Inicijuojame su SPECIFINIAIS TZT POSLINKIAIS
            # Jei tavo biblioteka naudoja kitus vardus, šis blokas juos sugaus
            params = {
                'port': 0,
                'cs': CS_PIN,
                'dc': DC_PIN,
                'rst': RST_PIN,
                'width': 240,
                'height': 320,
                'rotation': 0,
                'spi_speed_hz': 4000000
            }
            
            self.disp = st7789.ST7789(**params)
            
            # TZT 2.0" ekranų "Sniego" gydymas:
            # Dažniausiai reikia nustumti vaizdą per 0 arba 80 pikselių
            try:
                self.disp.offset_left = 0
                self.disp.offset_top = 0 # Jei bus juosta, pakeisim į 80
            except:
                pass

            self.disp.begin()
            
            # Priverstinis spalvų įjungimas
            self.disp.command(0x21) # INVON
            self.disp.command(0x11) # SLPOUT (Išjungti miegą)
            self.disp.command(0x29) # DISPON (Įjungti ekraną)

            print("[OK] Valdiklis paruoštas.")
        except Exception as e:
            print(f"[FAIL] Klaida: {e}")

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets", "neutral")
        self.frames = []
        self._prepare_frames()

    def _prepare_frames(self):
        """Paruošiame vaizdus: pasukame ir rezaisiname rankiniu būdu"""
        try:
            test_img = Image.new("RGB", (240, 320), (255, 0, 0)) # RAUDONA
            
            if os.path.exists(self.assets_path):
                files = sorted([f for f in os.listdir(self.assets_path) if f.endswith('.png')])
                for f in files[:20]:
                    img = Image.open(os.path.join(self.assets_path, f)).convert("RGB")
                    # Pasukame 90 laipsnių, kad gautume "Landscape" ant "Portrait" stiklo
                    img = img.resize((320, 240))
                    img = img.rotate(90, expand=True)
                    self.frames.append(img)
            
            if not self.frames:
                self.frames = [test_img]
                print("[WARN] Assets nerasti, rodau raudoną testą.")
            else:
                print(f"[OK] Užkrauta kadrų: {len(self.frames)}")
        except Exception as e:
            print(f"Klaida: {e}")

    def run(self):
        print("[*] SIUNČIU VAIZDĄ...")
        while True:
            for frame in self.frames:
                self.disp.display(frame)
                time.sleep(0.05)

if __name__ == "__main__":
    robot = EvilSonicGynimas()
    robot.run()
