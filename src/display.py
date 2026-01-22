import time
import os
import spidev
import RPi.GPIO as GPIO
import numpy as np
from PIL import Image
import asyncio

class EvilSonicDisplay:
    def __init__(self, assets_dir="/home/cm4/robot-project/src/assets/"):
        self.assets_dir = assets_dir
        self.current_state = "static"
        self.frames = {}
        self.frame_counter = 0
        
        # Pinai
        self.DC, self.RST = 24, 25
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([self.DC, self.RST], GPIO.OUT)

        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        # Padidiname iki 60MHz (CM4 tai palaiko, TZT ekranas irgi)
        self.spi.max_speed_hz = 60000000 
        self.spi.mode = 0b11 
        
        self.init_hw()
        self.load_assets()

    def write_cmd(self, cmd):
        GPIO.output(self.DC, GPIO.LOW)
        self.spi.writebytes([cmd])

    def write_data(self, data):
        GPIO.output(self.DC, GPIO.HIGH)
        if isinstance(data, int): data = [data]
        self.spi.writebytes(data)

    def init_hw(self):
        GPIO.output(self.RST, GPIO.LOW); time.sleep(0.1); GPIO.output(self.RST, GPIO.HIGH); time.sleep(0.1)
        self.write_cmd(0x01); time.sleep(0.15)
        self.write_cmd(0x11); time.sleep(0.1)
        self.write_cmd(0x3A); self.write_data(0x05) 
        # 0x70 nustato Landscape (gulsčią)
        self.write_cmd(0x36); self.write_data(0x70) 
        self.write_cmd(0x21); self.write_cmd(0x29)
        print("[OK] Ekranas paruoštas.")

    def load_assets(self):
        states = ["static", "speaking", "angry", "laughing", "shook"]
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_dir, state)
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    img = Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240))
                    img_np = np.array(img).astype(np.uint16)
                    # Optimizuotas RGB888 -> RGB565 konvertavimas per Numpy
                    color = ((img_np[:,:,0] & 0xF8) << 8) | ((img_np[:,:,1] & 0xFC) << 3) | (img_np[:,:,2] >> 3)
                    pixel_bytes = np.stack(((color >> 8).astype(np.uint8), (color & 0xFF).astype(np.uint8)), axis=-1).tobytes()
                    self.frames[state].append(pixel_bytes)

    def show_raw(self, pixel_bytes):
        # Nustatome piešimo langą: 320x240
        self.write_cmd(0x2A); self.write_data([0x00, 0x00, 0x01, 0x3F])
        self.write_cmd(0x2B); self.write_data([0x00, 0x00, 0x00, 0xEF])
        self.write_cmd(0x2C) 
        GPIO.output(self.DC, GPIO.HIGH)
        # Siunčiame visą buferį vienu kartu (modernūs dravieriai tai leidžia)
        self.spi.writebytes2(pixel_bytes)

    async def animate(self):
        while True:
            frames = self.frames.get(self.current_state, [])
            if not frames:
                await asyncio.sleep(0.1); continue
            
            # Logika emocijų išlaikymui
            if self.current_state in ["angry", "shook"]:
                idx = min(self.frame_counter, len(frames) - 1)
            else:
                idx = self.frame_counter % len(frames)
            
            # Naudojame writebytes2, kad būtų žaibiška
            await asyncio.to_thread(self.show_raw, frames[idx])
            self.frame_counter += 1
            await asyncio.sleep(0.04) # 25 FPS

    def set_state(self, new_state):
        if new_state in self.frames and new_state != self.current_state:
            self.current_state = new_state
            self.frame_counter = 0
