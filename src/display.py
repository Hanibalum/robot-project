import time
import os
import spidev
import RPi.GPIO as GPIO
import numpy as np
from PIL import Image
import threading

class EvilSonicDisplay:
    def __init__(self, assets_dir="/home/cm4/robot-project/src/assets/"):
        self.assets_dir = assets_dir
        self.current_state = "static"
        self.frame_buffer = []
        self.lock = threading.Lock()
        self.frame_counter = 0
        self.DC, self.RST = 24, 25
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.DC, self.RST], GPIO.OUT)

        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 32000000 
        self.spi.mode = 0b11 
        
        self._init_tzt_hardware()
        self.load_assets("static") 
        
        self.running = True
        self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self.render_thread.start()

    def _init_tzt_hardware(self):
        """Specifinė seka TZT 2.0 ekranams, kad jie 'atsidarytų'"""
        GPIO.output(self.RST, GPIO.LOW); time.sleep(0.1); GPIO.output(self.RST, GPIO.HIGH); time.sleep(0.1)
        
        cmds = [
            (0x01, None),      # Software reset
            (0x11, None),      # Sleep out
            (0x3A, [0x05]),    # Interface pixel format (16-bit)
            (0x36, [0x00]),    # MADCTL: Portrait
            (0x21, None),      # Inversion ON
            (0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33]), # Porch Setting
            (0xB7, [0x35]),    # Gate Control
            (0xBB, [0x19]),    # VCOM Setting
            (0xC0, [0x2C]),    # LCM Control
            (0x29, None)       # Display ON
        ]
        for cmd, data in cmds:
            GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([cmd])
            if data: GPIO.output(self.DC, GPIO.HIGH); self.spi.writebytes(data)
            time.sleep(0.1)

    def load_assets(self, state):
        path = os.path.join(self.assets_dir, state)
        new_frames = []
        if os.path.exists(path):
            files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
            for f in files:
                img = Image.open(os.path.join(path, f)).convert("RGB").resize((240, 320))
                img_data = np.array(img).astype(np.uint16)
                color = ((img_data[:,:,0] & 0xF8) << 8) | ((img_data[:,:,1] & 0xFC) << 3) | (img_data[:,:,2] >> 3)
                pixel_bytes = np.stack(((color >> 8).astype(np.uint8), (color & 0xFF).astype(np.uint8)), axis=-1).tobytes()
                new_frames.append(pixel_bytes)
        
        with self.lock:
            self.frame_buffer = new_frames
            self.frame_counter = 0

    def _render_loop(self):
        while self.running:
            with self.lock:
                if not self.frame_buffer: 
                    time.sleep(0.1); continue
                frame = self.frame_buffer[self.frame_counter % len(self.frame_buffer)]
            
            # Adresavimas (Fizinės koordinatės be rotacijos klaidų)
            GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([0x2A]); GPIO.output(self.DC, GPIO.HIGH); self.spi.writebytes([0, 0, 0, 239])
            GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([0x2B]); GPIO.output(self.DC, GPIO.HIGH); self.spi.writebytes([0, 0, 1, 63])
            GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([0x2C]); GPIO.output(self.DC, GPIO.HIGH)
            
            for i in range(0, len(frame), 4096):
                self.spi.writebytes(list(frame[i:i+4096]))
            
            self.frame_counter += 1
            time.sleep(0.04)

    def set_state(self, state):
        self.load_assets(state)

    async def animate(self):
        while self.running: await asyncio.sleep(1)
