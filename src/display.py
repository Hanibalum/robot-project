import st7789
from PIL import Image
import os
import asyncio
import RPi.GPIO as GPIO
import numpy as np
import time

class EvilSonicDisplay:
    def __init__(self, assets_dir="/home/cm4/robot-project/src/assets/"):
        self.assets_dir = assets_dir
        self.current_state = "static"
        self.frames = {}
        self.frame_counter = 0
        
        # Pinai (Pin 18->24, Pin 22->25, Pin 24->CS0)
        self.DC, self.RST, self.CS = 24, 25, 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([self.DC, self.RST], GPIO.OUT)

        # 1. Fizinis Reset
        GPIO.output(self.RST, GPIO.LOW); time.sleep(0.1); GPIO.output(self.RST, GPIO.HIGH)

        # 2. Inicializacija
        self.disp = st7789.ST7789(
            port=0, cs=self.CS, dc=self.DC, rst=self.RST,
            width=240, height=320, rotation=0, spi_speed_hz=40000000
        )
        self.disp.begin()
        self.disp.command(0x21) # Inversija
        self.disp.command(0x11) # Wake
        self.disp.command(0x29) # On

        self.load_assets()

    def load_assets(self):
        states = ["static", "speaking", "angry", "laughing", "shook"]
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_dir, state)
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    img = Image.open(os.path.join(path, f)).convert("RGB")
                    # Pasukame ir optimizuojame per Numpy
                    img = img.resize((320, 240)).rotate(90, expand=True)
                    self.frames[state].append(img)
            if not self.frames[state]:
                self.frames[state] = [Image.new('RGB', (240, 320), color=(0, 0, 100))]

    async def animate(self):
        print("[*] Ekrano animacija paleista (Numpy optimized).")
        while True:
            frames = self.frames.get(self.current_state, [])
            if frames:
                img = frames[self.frame_counter % len(frames)]
                # Naudojame greitą išvedimą
                await asyncio.to_thread(self.disp.display, img)
                self.frame_counter += 1
            await asyncio.sleep(0.04)

    def set_state(self, new_state):
        if new_state in self.frames and new_state != self.current_state:
            self.current_state = new_state
            self.frame_counter = 0
