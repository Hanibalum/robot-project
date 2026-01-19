import time
import os
import spidev
import RPi.GPIO as GPIO
from PIL import Image
import asyncio

class EvilSonicDisplay:
    def __init__(self, assets_dir="/home/cm4/robot-project/src/assets/"):
        self.assets_dir = assets_dir
        self.current_state = "static"
        self.frames = {}
        self.frame_counter = 0
        
        # --- APARATŪRINIAI PINAI (Fiziniai -> GPIO) ---
        self.DC = 24   # Pin 18
        self.RST = 25  # Pin 22
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([self.DC, self.RST], GPIO.OUT)

        # 1. Inicijuojame SPI tiesiogiai (Geležinis metodas)
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 40000000 
        self.spi.mode = 0b11 
        
        self.init_display_hardware()
        self.load_assets()

    def write_cmd(self, cmd):
        GPIO.output(self.DC, GPIO.LOW)
        self.spi.writebytes([cmd])

    def write_data(self, data):
        GPIO.output(self.DC, GPIO.HIGH)
        if isinstance(data, int): data = [data]
        self.spi.writebytes(data)

    def init_display_hardware(self):
        """Tiesioginis TZT 2.0 ekranų pažadinimas"""
        GPIO.output(self.RST, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.RST, GPIO.HIGH)
        time.sleep(0.1)
        
        self.write_cmd(0x01) # Software reset
        time.sleep(0.15)
        self.write_cmd(0x11) # Sleep out
        time.sleep(0.1)
        self.write_cmd(0x3A); self.write_data(0x05) 
        self.write_cmd(0x36); self.write_data(0x00) 
        self.write_cmd(0x21) # Inversion ON
        self.write_cmd(0x29) # Display ON
        print("[OK] Ekranas pažadintas sėkmingai.")

    def load_assets(self):
        """Užkrauna kadrus ir konvertuoja į ekranui tinkamą formatą"""
        states = ["static", "speaking", "angry", "laughing", "shook"]
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_dir, state)
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    try:
                        img = Image.open(os.path.join(path, f)).convert("RGB")
                        # Rezaisinam ir pasukam 90 laipsnių rankiniu būdu
                        img = img.resize((240, 320)).rotate(90, expand=True)
                        self.frames[state].append(img)
                    except: pass
            
            if not self.frames[state]:
                # Jei neranda nuotraukų - mėlynas kvadratas
                self.frames[state] = [Image.new('RGB', (320, 240), color=(0, 0, 150))]

    def display_raw(self, img):
        """Siunčia paruoštą vaizdą tiesiai į VRAM"""
        # Konvertuojame PIL vaizdą į RGB565 formatą
        pixel_data = []
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = img.getpixel((x, y))
                color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                pixel_data.append(color >> 8)
                pixel_data.append(color & 0xFF)
        
        self.write_cmd(0x2A); self.write_data([0, 0, 0, 239])
        self.write_cmd(0x2B); self.write_data([0, 0, 1, 63])
        self.write_cmd(0x2C)
        
        GPIO.output(self.DC, GPIO.HIGH)
        chunk_size = 4096
        for i in range(0, len(pixel_data), chunk_size):
            self.spi.writebytes(pixel_data[i:i+chunk_size])

    async def animate(self):
        print("[*] Animacija paleista...")
        while True:
            frames = self.frames.get(self.current_state, [])
            if frames:
                img = frames[self.frame_counter % len(frames)]
                # Naudojame tiesioginį išvedimą į ekraną
                await asyncio.to_thread(self.display_raw, img)
                self.frame_counter += 1
            await asyncio.sleep(0.04) # 25 FPS

    def set_state(self, new_state):
        if new_state in self.frames and new_state != self.current_state:
            self.current_state = new_state
            self.frame_counter = 0
