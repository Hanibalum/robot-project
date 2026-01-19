import st7789
from PIL import Image
import os
import asyncio
import RPi.GPIO as GPIO
import time

class EvilSonicDisplay:
    def __init__(self, assets_dir="/home/cm4/robot-project/src/assets/"):
        self.assets_dir = assets_dir
        self.current_state = "static"
        self.frames = {}
        self.frame_counter = 0
        
        # --- APARATŪRINIAI PINAI ---
        self.DC_GPIO = 24  # Pin 18
        self.RST_GPIO = 25 # Pin 22
        self.CS_DEVICE = 0 # Pin 24

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.RST_GPIO, GPIO.OUT)

        # 1. Fizinis RESET
        GPIO.output(self.RST_GPIO, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.RST_GPIO, GPIO.HIGH)
        time.sleep(0.1)

        # 2. Inicijuojame ST7789
        # SVARBU: TZT 2.0" ekranams dažnai reikia nustatyti x_offset ir y_offset
        self.disp = st7789.ST7789(
            port=0,
            cs=self.CS_DEVICE,
            dc=self.DC_GPIO,
            rst=self.RST_GPIO,
            width=240,
            height=320,
            rotation=0,        # Naudojame 0, kad išvengtume bibliotekos klaidų
            spi_speed_hz=8000000
        )
        
        self.disp.begin()
        
        # 3. TZT SPECIFINIAI NUSTATYMAI
        self.disp.command(0x21) # Spalvų inversija
        
        # Nustatome poslinkį (dažniausiai 2.0" ekranams tai yra x=0, y=80 arba y=35)
        # Šis kodas naudos 320x240 langą viduryje 320x320 valdiklio
        try:
            self.disp.offset_left = 0
            self.disp.offset_top = 80 # PAKEISK Į 35 JEI VAIZDAS BUS PERSISKYRĘS
        except:
            pass

        self.load_assets()

    def load_assets(self):
        """Užkrauna ir pasuka nuotraukas 90 laipsnių"""
        states = ["static", "speaking", "angry", "laughing", "shook"]
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_dir, state)
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    try:
                        img = Image.open(os.path.join(path, f)).convert("RGB")
                        # Pritaikome tavo gulsčiam vaizdui:
                        # Pirmiausia resize iki gulsčio 320x240, tada pasukam 90 laipsnių į 240x320
                        img = img.resize((320, 240))
                        img = img.rotate(90, expand=True)
                        self.frames[state].append(img)
                    except Exception as e:
                        print(f"Klaida kraunant {f}: {e}")
            
            if not self.frames[state]:
                # Avarinis žalias kadras testui
                err_img = Image.new('RGB', (240, 320), color=(0, 255, 0))
                self.frames[state].append(err_img)

    def get_next_frame(self):
        frames = self.frames.get(self.current_state, [])
        if not frames: return Image.new('RGB', (240, 320), color=(0, 0, 0))
        idx = self.frame_counter % len(frames)
        return frames[idx]

    async def animate(self):
        print("[*] Evil Sonic animacija paleista...")
        while True:
            img = self.get_next_frame()
            self.disp.display(img)
            self.frame_counter += 1
            await asyncio.sleep(0.05)

    def set_state(self, new_state):
        if new_state in self.frames and new_state != self.current_state:
            print(f"[DISPLAY] Keiciama emocija i: {new_state}")
            self.current_state = new_state
            self.frame_counter = 0
