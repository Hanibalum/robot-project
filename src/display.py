import time
import os
import spidev
import RPi.GPIO as GPIO
import numpy as np
from PIL import Image
import threading
from itertools import cycle

class EvilSonicDisplay:
    def __init__(self, assets_dir="/home/cm4/robot-project/src/assets/"):
        self.assets_dir = assets_dir
        self.current_state = "static"
        self.frame_buffer = []
        self.lock = threading.Lock()
        
        # Pinai
        self.DC, self.RST = 24, 25
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.DC, self.RST], GPIO.OUT)

        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 40000000 
        self.spi.mode = 0b11 
        
        self._init_st7789()
        self.load_assets("static") # Užkraunam pradinę emociją
        
        # Paleidžiame vaizdą TIKROJE gijoje (ne asyncio)
        self.thread = threading.Thread(target=self._render_loop, daemon=True)
        self.thread.start()

    def _init_st7789(self):
        GPIO.output(self.RST, GPIO.LOW); time.sleep(0.1); GPIO.output(self.RST, GPIO.HIGH); time.sleep(0.1)
        for cmd, data in [(0x01, None), (0x11, None), (0x3A, [0x05]), (0x36, [0x70]), (0x21, None), (0x29, None)]:
            GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([cmd])
            if data: GPIO.output(self.DC, GPIO.HIGH); self.spi.writebytes(data)
            time.sleep(0.1)

    def load_assets(self, state):
        path = os.path.join(self.assets_dir, state)
        new_frames = []
        if os.path.exists(path):
            files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
            for f in files:
                img = Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240))
                # Konvertuojame į RGB565 formatą iš anksto
                img_data = np.array(img).astype(np.uint16)
                color = ((img_data[:,:,0] & 0xF8) << 8) | ((img_data[:,:,1] & 0xFC) << 3) | (img_data[:,:,2] >> 3)
                pixel_bytes = np.stack(((color >> 8).astype(np.uint8), (color & 0xFF).astype(np.uint8)), axis=-1).tobytes()
                new_frames.append(pixel_bytes)
        
        with self.lock:
            self.frame_buffer = new_frames
            self.current_state = state

    def _render_loop(self):
        """Šis ciklas sukasi nepriklausomai nuo kito kodo"""
        while True:
            with self.lock:
                frames = list(self.frame_buffer)
            
            if not frames:
                time.sleep(0.1); continue
                
            for frame in frames:
                # Siunčiame į ekraną
                GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([0x2A]); GPIO.output(self.DC, GPIO.HIGH); self.spi.writebytes([0, 0, 0, 1, 0x3F])
                GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([0x2B]); GPIO.output(self.DC, GPIO.HIGH); self.spi.writebytes([0, 0, 0, 0, 0xEF])
                GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([0x2C]); GPIO.output(self.DC, GPIO.HIGH)
                for i in range(0, len(frame), 4096):
                    self.spi.writebytes(list(frame[i:i+4096]))
                
                # Fiksuotas greitis be jokių vėlavimų
                time.sleep(0.04)

    def set_state(self, state):
        # Šią funkciją kvies main.py
        threading.Thread(target=self.load_assets, args=(state,), daemon=True).start()
