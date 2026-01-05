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
        time.sleep(0.1)
        GPIO.output(RST_GPIO, GPIO.HIGH)
        time.sleep(0.1)

        try:
            # Iniciuojame TIKSLIAI 240x320 be jokių rotacijų
            self.disp = st7789.ST7789(
                port=0, cs=CS_DEVICE, dc=DC_GPIO, rst=RST_GPIO,
                width=240, height=320, rotation=0, 
                spi_speed_hz=8000000
            )
            self.disp.begin()
            
            # Bandome įjungti inversiją per žemo lygio komandą (kad nemestų klaidos)
            try: self.disp.command(0x21)
            except: pass

            self.display_active = True
            print("[OK] Ekranas inicijuotas.")
        except Exception as e:
            print(f"[FAIL] {e}")

        self.frames = []
        self._load_and_prepare_frames()

    def _load_and_prepare_frames(self):
        """Užkrauna vaizdus ir rankiniu būdu sutvarko sniegą (Offset)"""
        try:
            files = sorted([f for f in os.listdir(self.assets_path) if f.endswith('.png')])
            if not files: raise Exception("Tuscia")
            
            for f in files[:20]:
                img = Image.open(os.path.join(self.assets_path, f)).convert("RGB")
                # 1. Sukuriame juodą drobę (pilną valdiklio atmintį)
                canvas = Image.new("RGB", (240, 320), (0, 0, 0))
                # 2. Paruošiame akis (320x240) ir pasukame jas
                eyes = img.resize((320, 240)).rotate(90, expand=True)
                # 3. Įklijuojame akis į drobę, pastumdami jas nuo triukšmo zonos
                # Jei sniegas yra apačioje, čia keičiame (0, 0) į (0, -80) arba (0, 80)
                canvas.paste(eyes, (0, 0)) 
                self.frames.append(canvas)
            print(f"[OK] Paruošta: {len(self.frames)} kadrų.")
        except:
            # AVARINIS VAIZDAS: Jei niekas neveikia, bent jau matysime spalvą
            img = Image.new("RGB", (240, 320), (255, 0, 0))
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
