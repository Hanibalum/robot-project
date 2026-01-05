import time
import os
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import st7789

# --- TAVO FIZINIAI KONTAKTAI ---
# Pin 24 (CS) -> cs=0
# Pin 18 (DC) -> GPIO 24
# Pin 22 (RST) -> GPIO 25
DC_PIN  = 24
RST_PIN = 25
CS_PIN  = 0 

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicRescue:
    def __init__(self):
        print("[*] REANIMACIJA: Pažadinimo komandos siunčiamos...")
        
        # 1. Fizinis RESET (Ilgas, kad valdiklis tikrai persikrautų)
        GPIO.setup(RST_PIN, GPIO.OUT)
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.5)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.5)

        try:
            # 2. Inicijuojame be jokių automatinių rotacijų
            self.disp = st7789.ST7789(
                port=0, 
                cs=CS_PIN, 
                dc=DC_PIN, 
                rst=RST_PIN, 
                width=240, 
                height=320, 
                rotation=0, 
                spi_speed_hz=4000000 
            )
            self.disp.begin()
            
            # --- AGRESYVUS PAŽADINIMAS (Tiesioginės instrukcijos) ---
            self.disp.command(0x11) # Sleep out (Išeiti iš miego)
            time.sleep(0.1)
            self.disp.command(0x21) # Inversion ON (Kad juoda būtų juoda)
            self.disp.command(0x29) # Display ON (Įjungti vaizdą)
            
            print("[OK] Valdiklis pažadintas.")
        except Exception as e:
            print(f"[FAIL] Klaida: {e}")

        self.assets_path = os.path.join(os.path.dirname(__file__), "assets", "neutral")
        self.frames = []
        self._load_emergency_frame()

    def _load_emergency_frame(self):
        """Sukuriam ryškų vaizdą, kurį matytum net pro 'sniegą'"""
        # RAUDONAS kvadratas per visą centrą
        img = Image.new("RGB", (240, 320), (255, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle((40, 40, 200, 280), outline="white", fill="white")
        d.text((60, 150), "SPI OK: LAUKIU", fill="red")
        
        # Bandome įkelti bent vieną tavo nuotrauką pasuktą
        try:
            files = [f for f in os.listdir(self.assets_path) if f.endswith('.png')]
            if files:
                eye = Image.open(os.path.join(self.assets_path, files[0])).convert("RGB")
                eye = eye.resize((320, 240)).rotate(90, expand=True)
                self.frames.append(eye)
        except:
            pass
            
        if not self.frames:
            self.frames = [img]

    def run(self):
        print("[*] Siunčiu duomenis... Žiūrėk į ekraną!")
        while True:
            for frame in self.frames:
                self.disp.display(frame)
                time.sleep(0.1)

if __name__ == "__main__":
    robot = EvilSonicRescue()
    robot.run()
