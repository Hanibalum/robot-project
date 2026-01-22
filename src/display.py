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
        
        # --- APARATŪRINIAI PINAI (Fiziniai -> GPIO) ---
        self.DC = 24   # Pin 18 (Griežtai tavo nurodymas)
        self.RST = 25  # Pin 22
        # CS valdomas per spidev(0, 0) -> Pin 24
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([self.DC, self.RST], GPIO.OUT)

        # Inicijuojame SPI tiesiogiai (Tas pats metodas, kur rodė mėlyną spalvą)
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 40000000 
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
        """Gamyklinis ST7789 pažadinimas"""
        GPIO.output(self.RST, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.RST, GPIO.HIGH)
        time.sleep(0.1)
        
        self.write_cmd(0x01) # SW reset
        time.sleep(0.15)
        self.write_cmd(0x11) # Sleep out
        time.sleep(0.1)
        self.write_cmd(0x3A); self.write_data(0x05) # 16-bit color
        # 0x00 - Portrait, 0x70 - Landscape (Evil Sonic stilius)
        self.write_cmd(0x36); self.write_data(0x00) 
        self.write_cmd(0x21) # Inversion ON
        self.write_cmd(0x29) # Display ON
        print("[OK] ST7789 pažadintas tiesioginiu būdu.")

    def load_assets(self):
        """Užkrauna kadrus ir paverčia juos į greitą Hardware formatą (Numpy)"""
        states = ["static", "speaking", "angry", "laughing", "shook"]
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_dir, state)
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    try:
                        img = Image.open(os.path.join(path, f)).convert("RGB")
                        # 2.0" ekranas: 240x320. Pasukame 90 laipsnių patys.
                        img = img.resize((240, 320)).rotate(90, expand=True)
                        img_np = np.array(img).astype(np.uint16)
                        # RGB888 -> RGB565 (Hardware lygis)
                        color = ((img_np[:,:,0] & 0xF8) << 8) | ((img_np[:,:,1] & 0xFC) << 3) | (img_np[:,:,2] >> 3)
                        pixel_bytes = np.stack(((color >> 8).astype(np.uint8), (color & 0xFF).astype(np.uint8)), axis=-1).tobytes()
                        self.frames[state].append(pixel_bytes)
                    except: pass
            
            if not self.frames[state]:
                # Jei nuotraukų nėra - tamsiai raudonas kvadratas (Evil Sonic testas)
                red_pixels = [0xF8, 0x00] * (240 * 320)
                self.frames[state] = [bytes(red_pixels)]

    def draw_raw(self, pixel_bytes):
        """Siunčiame duomenis į VRAM be jokių vėlinimų"""
        self.write_cmd(0x2A); self.write_data([0, 0, 0, 239]) # X
        self.write_cmd(0x2B); self.write_data([0, 0, 1, 63])  # Y
        self.write_cmd(0x2C)
        GPIO.output(self.DC, GPIO.HIGH)
        # Skaidome duomenis į blokus (spidev limitas yra ~4096)
        for i in range(0, len(pixel_bytes), 4096):
            self.spi.writebytes(list(pixel_bytes[i:i+4096]))

    async def animate(self):
        print("[*] Animacijos ciklas aktyvuotas.")
        while True:
            frames = self.frames.get(self.current_state, [])
            if frames:
                data = frames[self.frame_counter % len(frames)]
                # Naudojame to_thread, kad SPI duomenų siuntimas neužšaldytų Gemini
                await asyncio.to_thread(self.draw_raw, data)
                self.frame_counter += 1
            await asyncio.sleep(0.04) # ~25 FPS

    def set_state(self, new_state):
        if new_state in self.frames and new_state != self.current_state:
            self.current_state = new_state
            self.frame_counter = 0
