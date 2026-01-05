import asyncio
import os
import random
import RPi.GPIO as GPIO
from PIL import Image
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- APARATŪROS NUSTATYMAI (Pagal tavo nurodytus Pinus) ---
# CS - Pin 24 (GPIO 8 -> device 0)
# DC - Pin 18 (GPIO 24)
# RST - Pin 22 (GPIO 25)
DC_GPIO, RST_GPIO, CS_DEVICE = 24, 25, 0

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class EvilSonicGynimas:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_path = os.path.join(self.base_dir, "assets")
        self.frames = []
        self.display_active = False
        
        # 1. Ekrano kėlimas (Pats pirmas darbas!)
        try:
            # Bandome inicijuoti ekraną
            self.serial_spi = spi(port=0, device=CS_DEVICE, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO)
            self.device = st7789(self.serial_spi, width=240, height=320, rotation=1)
            self.device.set_inversion(True)
            self.display_active = True
            print("[OK] Ekranas inicijuotas.")
        except Exception as e:
            print(f"[KLAIDA] Ekranas: {e}")

        # Užkrauname "neutral" emociją iškart
        self._load_emotion("neutral")

    def _load_emotion(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            if not files: raise Exception("Nėra PNG failų")
            self.frames = [Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240)) for f in files]
            print(f"[OK] Užkrauta: {emotion}")
        except:
            # Jei neranda tavo failų, sukuriam atsarginį vaizdą
            img = Image.new("RGB", (320, 240), (0, 0, 255)) # Mėlynas fonas
            self.frames = [img]
            print(f"[WARN] Nerasti assets/{emotion}. Rodomas testinis vaizdas.")

    async def animation_loop(self):
        """Šis ciklas sukasi nepriklausomai nuo visko"""
        print("[*] Animacija paleista.")
        while self.display_active:
            # Saugiai sukam kadrus
            current_set = list(self.frames)
            for frame in current_set:
                self.device.display(frame)
                await asyncio.sleep(0.05) # 20 FPS

    async def main_logic(self):
        """Čia imituojame roboto veiklą, kad niekas nepakibtų"""
        print("[OK] Robotas paruoštas gynimui.")
        while True:
            # Kas 15 sekundžių imituojame, kad robotas "kažką suprato"
            await asyncio.sleep(15)
            print("[DI] Analizuoju aplinką...")
            # Čia gali pridėti UART komandą arba Gemini užklausą vėliau
            # Dabar svarbiausia - stabilumas

async def main():
    robot = EvilSonicGynimas()
    # Paleidžiame animaciją ir logiką kartu
    await asyncio.gather(
        robot.animation_loop(),
        robot.main_logic()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        GPIO.cleanup()

