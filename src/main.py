import asyncio
import os
import RPi.GPIO as GPIO
import st7789
from PIL import Image, ImageDraw

# --- TIKSLŪS TAVO KONTAKTAI (GPIO numeriai) ---
# Pin 24 = GPIO 8 (CS0) -> device=0
# Pin 18 = GPIO 24 (DC)
# Pin 22 = GPIO 25 (RST)
DC_GPIO = 24
RST_GPIO = 25
CS_DEVICE = 0  

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicRescue:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets")
        self.display_active = False
        
        try:
            # TZT 2.0" ekranams geriausiai veikia šis inicializavimas
            self.disp = st7789.ST7789(
                port=0,
                cs=CS_DEVICE,
                dc=DC_GPIO,
                rst=RST_GPIO,
                width=320,      # Pakeista tvarka stabiliam darbui
                height=240,
                rotation=90,    # Gulsčias režimas
                spi_speed_hz=4000000 # 4MHz - lėtai, bet saugiai
            )
            self.disp.begin()
            
            # SVARBU: TZT moduliams reikia šių dviejų eilučių, kad dingtų "triukšmas"
            self.disp.set_inversion(True)
            
            self.display_active = True
            print("[OK] Ekranas inicijuotas su poslinkio pataisymais.")
        except Exception as e:
            print(f"[KLAIDA] Ekranas: {e}")

        self.frames = []
        self._load_emotion("neutral")

    def _load_emotion(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            if not files: raise Exception("Aplankas tuščias")
            # Krauname ir įsitikiname, kad dydis tinka
            self.frames = [Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240)) for f in files]
            print(f"[OK] Užkrauta: {emotion} ({len(self.frames)} k.)")
        except:
            # Jei neranda failų, rodomas tekstas, kad nupieštų kažką
            img = Image.new("RGB", (320, 240), (0, 100, 0)) # Tamsiai žalia
            d = ImageDraw.Draw(img)
            d.text((100, 110), "SYSTEM READY", fill="white")
            self.frames = [img]

    async def animation_loop(self):
        print("[*] Animacija paleista.")
        while self.display_active:
            for frame in self.frames:
                self.disp.display(frame)
                await asyncio.sleep(0.06)

    async def heartbeat(self):
        """Imituojame darbą terminale"""
        while True:
            print("[STATUS] Robotas veikia asinhroniniu režimu...")
            await asyncio.sleep(10)

async def main():
    robot = EvilSonicRescue()
    await asyncio.gather(
        robot.animation_loop(),
        robot.heartbeat()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        GPIO.cleanup()
