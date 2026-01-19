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
        
        # Tavo fiziniai kontaktai
        self.DC_GPIO = 24
        self.RST_GPIO = 25
        self.CS_DEVICE = 0 

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.RST_GPIO, GPIO.OUT)

        # 1. Fizinis RESET (Privalomas tavo ekranui)
        GPIO.output(self.RST_GPIO, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.RST_GPIO, GPIO.HIGH)
        time.sleep(0.1)

        # 2. Inicijuojame ST7789 be rotacijos (0), kad nemestų klaidos
        self.disp = st7789.ST7789(
            port=0, cs=self.CS_DEVICE, dc=self.DC_GPIO, rst=self.RST_GPIO,
            width=240, height=320, rotation=0, 
            spi_speed_hz=8000000
        )
        self.disp.begin()
        
        # 3. Tiesioginės komandos pažadinimui (INVON, SLPOUT, DISPON)
        self.disp.command(0x21) 
        self.disp.command(0x11)
        self.disp.command(0x29)
        
        # Užkrauname nuotraukas
        self.load_assets()

    def load_assets(self):
        """Užkrauna nuotraukas ir jas pasuka rankiniu būdu"""
        states = ["static", "speaking", "angry", "laughing", "shook"]
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_dir, state)
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    try:
                        img = Image.open(os.path.join(path, f)).convert("RGB")
                        # Pritaikome tavo ekranui: rezaisinam ir pasukame patys
                        img = img.resize((320, 240))
                        img = img.rotate(90, expand=True)
                        self.frames[state].append(img)
                    except Exception as e:
                        print(f"Error loading {f}: {e}")
            
            if not self.frames[state]:
                # Avarinis vaizdas, jei aplankas tuščias
                img = Image.new('RGB', (240, 320), color=(0, 0, 150))
                self.frames[state].append(img)

    def get_next_frame(self):
        """Jules parašyta animacijos logika"""
        frames = self.frames.get(self.current_state, [])
        if not frames: return Image.new('RGB', (240, 320), color=(0, 0, 0))
        
        total_frames = len(frames)
        idx = self.frame_counter % total_frames
        return frames[idx]

    async def animate(self):
        """Pagrindinis vaizdo ciklas"""
        print("[*] Evil Sonic animacija paleista...")
        while True:
            img = self.get_next_frame()
            self.disp.display(img)
            self.frame_counter += 1
            await asyncio.sleep(0.05) # 20 FPS

    def set_state(self, new_state):
        if new_state in self.frames and new_state != self.current_state:
            print(f"[DISPLAY] Keiciama emocija i: {new_state}")
            self.current_state = new_state
            self.frame_counter = 0
