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
        self.spi.max_speed_hz = 32000000 
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
        # Fizinis Reset
        GPIO.output(self.RST, GPIO.LOW); time.sleep(0.2); GPIO.output(self.RST, GPIO.HIGH); time.sleep(0.2)
        
        self.write_cmd(0x01) # Software Reset
        time.sleep(0.15)
        self.write_cmd(0x11) # Sleep Out
        time.sleep(0.1)
        
        # TZT 2.0" Gamykliniai nustatymai
        self.write_cmd(0x3A); self.write_data(0x05) # 16-bit color
        self.write_cmd(0x36); self.write_data(0x00) # MADCTL: Normal orientation
        self.write_cmd(0x21) # Inversion ON (TZT specifika)
        self.write_cmd(0xB2); self.write_data([0x0C, 0x0C, 0x00, 0x33, 0x33]) # Porch Setting
        self.write_cmd(0x35); self.write_data(0x00) # Tearing Effect ON
        
        self.write_cmd(0x29) # Display ON
        print("[OK] Ekranas pažadintas gamykliniu režimu.")

    def load_assets(self):
        states = ["static", "speaking", "angry", "laughing", "shook"]
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_dir, state)
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    img = Image.open(os.path.join(path, f)).convert("RGB")
                    # Pasukame 90 laipsnių, kad gautume 320x240 vaizdą
                    img = img.resize((320, 240)).rotate(90, expand=True)
                    img_data = np.array(img).astype(np.uint16)
                    # RGB888 -> RGB565 (Inžinerinis standartas)
                    color = ((img_data[:,:,0] & 0xF8) << 8) | ((img_data[:,:,1] & 0xFC) << 3) | (img_data[:,:,2] >> 3)
                    pixel_bytes = np.stack(((color >> 8).astype(np.uint8), (color & 0xFF).astype(np.uint8)), axis=-1).tobytes()
                    self.frames[state].append(pixel_bytes)
            
            if not self.frames[state]:
                # Jei nėra assets, rodome MĖLYNĄ kadrą kaip testą
                blank = Image.new('RGB', (240, 320), color=(0, 0, 255))
                img_data = np.array(blank).astype(np.uint16)
                color = ((img_data[:,:,0] & 0xF8) << 8) | ((img_data[:,:,1] & 0xFC) << 3) | (img_data[:,:,2] >> 3)
                self.frames[state] = [np.stack(((color >> 8).astype(np.uint8), (color & 0xFF).astype(np.uint8)), axis=-1).tobytes()]

    def show_raw(self, pixel_bytes):
        # Column address: 0 to 239
        self.write_cmd(0x2A); self.write_data([0x00, 0x00, 0x00, 0xEF])
        # Row address: 0 to 319
        self.write_cmd(0x2B); self.write_data([0x00, 0x00, 0x01, 0x3F])
        self.write_cmd(0x2C) 
        
        GPIO.output(self.DC, GPIO.HIGH)
        chunk_size = 4096
        for i in range(0, len(pixel_bytes), chunk_size):
            self.spi.writebytes(list(pixel_bytes[i:i+chunk_size]))

    async def animate(self):
        print("[*] Animacija paleista.")
        while True:
            frames = self.frames.get(self.current_state, [])
            if frames:
                data = frames[self.frame_counter % len(frames)]
                await asyncio.to_thread(self.show_raw, data)
                self.frame_counter += 1
            await asyncio.sleep(0.04)

    def set_state(self, new_state):
        if new_state in self.frames and new_state != self.current_state:
            self.current_state = new_state
            self.frame_counter = 0
