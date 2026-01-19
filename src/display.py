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
        
        # Pinai: DC=24 (Pin 18), RST=25 (Pin 22), CS=0 (Pin 24)
        self.DC, self.RST = 24, 25
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.DC, self.RST], GPIO.OUT)

        # SPI tiesioginis valdymas
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 32000000 
        self.spi.mode = 0b11 # Mode 3 (Butina TZT)
        
        self.init_display()
        self.load_assets()

    def write_cmd(self, cmd):
        GPIO.output(self.DC, GPIO.LOW)
        self.spi.writebytes([cmd])

    def write_data(self, data):
        GPIO.output(self.DC, GPIO.HIGH)
        if isinstance(data, int): data = [data]
        self.spi.writebytes(data)

    def init_display(self):
        # Fizinis Reset
        GPIO.output(self.RST, GPIO.LOW); time.sleep(0.1); GPIO.output(self.RST, GPIO.HIGH); time.sleep(0.1)
        self.write_cmd(0x01); time.sleep(0.15) # SW reset
        self.write_cmd(0x11); time.sleep(0.1)  # Sleep out
        self.write_cmd(0x3A); self.write_data(0x05) # 16-bit color
        self.write_cmd(0x36); self.write_data(0x00) # Portrait
        self.write_cmd(0x21) # Inversion ON
        self.write_cmd(0x29) # Display ON
        print("[OK] Ekranas pazadintas tiesiogiai per spidev.")

    def load_assets(self):
        states = ["static", "speaking", "angry", "laughing", "shook"]
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_dir, state)
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    img = Image.open(os.path.join(path, f)).convert("RGB")
                    # Pasukame vaizda, kad tilptu i ekrana
                    img = img.resize((240, 320)).rotate(90, expand=True)
                    # Konvertuojame i RGB565 (Hardware formatas)
                    pixel_bytes = []
                    for y in range(img.height):
                        for x in range(img.width):
                            r, g, b = img.getpixel((x, y))
                            color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                            pixel_bytes.append(color >> 8)
                            pixel_bytes.append(color & 0xFF)
                    self.frames[state].append(pixel_bytes)
            
            if not self.frames[state]:
                # Jei nera assets - darysim RAUDONA testa
                self.frames[state] = [[0xF8, 0x00] * (240 * 320)]

    async def animate(self):
        print("[*] Animacija sukasi...")
        while True:
            frames = self.frames.get(self.current_state, [])
            if frames:
                data = frames[self.frame_counter % len(frames)]
                # Siunciame i VRAM
                self.write_cmd(0x2A); self.write_data([0, 0, 0, 239])
                self.write_cmd(0x2B); self.write_data([0, 0, 1, 63])
                self.write_cmd(0x2C)
                GPIO.output(self.DC, GPIO.HIGH)
                # Skaidome i blokus SPI siuntimui
                for i in range(0, len(data), 4096):
                    self.spi.writebytes(data[i:i+4096])
                self.frame_counter += 1
            await asyncio.sleep(0.04)

    def set_state(self, new_state):
        if new_state in self.frames and new_state != self.current_state:
            self.current_state = new_state
            self.frame_counter = 0
