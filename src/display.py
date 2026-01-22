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
        
        # Tavo pinai (GPIO)
        self.DC = 24  # Pin 18
        self.RST = 25 # Pin 22
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([self.DC, self.RST], GPIO.OUT)

        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        # 24MHz yra saugus greitis, kad vaizdas nesilietų
        self.spi.max_speed_hz = 24000000 
        self.spi.mode = 0b11 
        
        self.init_hardware()
        self.load_assets()

    def write_cmd(self, cmd):
        GPIO.output(self.DC, GPIO.LOW)
        self.spi.writebytes([cmd])

    def write_data(self, data):
        GPIO.output(self.DC, GPIO.HIGH)
        if isinstance(data, int): data = [data]
        self.spi.writebytes(data)

    def init_hardware(self):
        """Tikslus TZT 2.0 inicijavimas gulsčiam režimui"""
        GPIO.output(self.RST, GPIO.LOW); time.sleep(0.1); GPIO.output(self.RST, GPIO.HIGH); time.sleep(0.1)
        self.write_cmd(0x01); time.sleep(0.15) # SW reset
        self.write_cmd(0x11); time.sleep(0.1)  # Sleep out
        self.write_cmd(0x3A); self.write_data(0x05) # 16-bit color
        
        # 0x70 nustato gulsčią vaizdą (Landscape) ir ištaiso apvertimą
        self.write_cmd(0x36); self.write_data(0x70) 
        
        self.write_cmd(0x21) # Inversion ON
        self.write_cmd(0x29) # Display ON
        print("[OK] ST7789 suderintas.")

    def load_assets(self):
        """Krauname Sonic emocijas ir konvertuojame i RGB565"""
        states = ["static", "speaking", "angry", "laughing", "shook"]
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_dir, state)
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    try:
                        img = Image.open(os.path.join(path, f)).convert("RGB")
                        # Gulsčias vaizdas 320x240
                        img = img.resize((320, 240))
                        img_np = np.array(img).astype(np.uint16)
                        # RGB888 -> RGB565 (Inžinerinis metodas)
                        color = ((img_np[:,:,0] & 0xF8) << 8) | ((img_np[:,:,1] & 0xFC) << 3) | (img_np[:,:,2] >> 3)
                        pixel_bytes = np.stack(((color >> 8).astype(np.uint8), (color & 0xFF).astype(np.uint8)), axis=-1).tobytes()
                        self.frames[state].append(pixel_bytes)
                    except: pass
            
            if not self.frames[state]:
                # Jei nera assets - mėlynas testinis kvadratas
                blue_pixels = [0x00, 0x1F] * (320 * 240)
                self.frames[state] = [bytes(blue_pixels)]

    def draw_frame(self, pixel_bytes):
        """Ištaisyti rėmeliai: X: 0-319, Y: 0-239"""
        self.write_cmd(0x2A); self.write_data([0x00, 0x00, 0x01, 0x3F]) # X: 0 iki 319
        self.write_cmd(0x2B); self.write_data([0x00, 0x00, 0x00, 0xEF]) # Y: 0 iki 239
        self.write_cmd(0x2C) 
        GPIO.output(self.DC, GPIO.HIGH)
        for i in range(0, len(pixel_bytes), 4096):
            self.spi.writebytes(list(pixel_bytes[i:i+4096]))

    async def animate(self):
        while True:
            frames = self.frames.get(self.current_state, [])
            if frames:
                data = frames[self.frame_counter % len(frames)]
                await asyncio.to_thread(self.draw_raw if hasattr(self, 'draw_raw') else self.draw_frame, data)
                self.frame_counter += 1
            await asyncio.sleep(0.05)

    def set_state(self, new_state):
        if new_state in self.frames and new_state != self.current_state:
            self.current_state = new_state
            self.frame_counter = 0
