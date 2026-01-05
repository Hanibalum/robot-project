import RPi.GPIO as GPIO
import time
import spidev
import os
from PIL import Image

# --- KONTAKTAI (TAVO PATIKRINTI) ---
DC = 24
RST = 25
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([DC, RST], GPIO.OUT)

class TZT_Display:
    def __init__(self):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 40000000 
        self.spi.mode = 0b11 

    def write_cmd(self, cmd):
        GPIO.output(DC, GPIO.LOW)
        self.spi.writebytes([cmd])

    def write_data(self, data):
        GPIO.output(DC, GPIO.HIGH)
        if isinstance(data, int): data = [data]
        self.spi.writebytes(data)

    def init(self):
        GPIO.output(RST, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST, GPIO.HIGH)
        time.sleep(0.1)
        self.write_cmd(0x01) # Reset
        time.sleep(0.15)
        self.write_cmd(0x11) # Sleep out
        time.sleep(0.1)
        self.write_cmd(0x3A) ; self.write_data(0x05) 
        self.write_cmd(0x36) ; self.write_data(0x00) 
        self.write_cmd(0x21) # Inversion ON
        self.write_cmd(0x29) # Display ON
        print("[OK] Ekranas paruoštas.")

    def show(self, pil_img):
        # Pritaikome vaizdą tavo ekranui
        img = pil_img.resize((240, 320)).rotate(90, expand=True)
        rgb888 = img.convert("RGB")
        pixel_data = []
        # Greita konversija į RGB565 formatą
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = rgb888.getpixel((x, y))
                color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                pixel_data.append(color >> 8)
                pixel_data.append(color & 0xFF)
        
        self.write_cmd(0x2A) ; self.write_data([0, 0, 0, 239])
        self.write_cmd(0x2B) ; self.write_data([0, 0, 1, 63])
        self.write_cmd(0x2C) 
        
        GPIO.output(DC, GPIO.HIGH)
        chunk_size = 4096
        for i in range(0, len(pixel_data), chunk_size):
            self.spi.writebytes(pixel_data[i:i+chunk_size])

# --- PAGRINDINĖ PROGRAMA ---
def run_robot():
    tzt = TZT_Display()
    tzt.init()
    
    # Kelias iki tavo nuotraukų
    assets_dir = os.path.join(os.path.dirname(__file__), "assets", "neutral")
    
    try:
        files = sorted([f for f in os.listdir(assets_dir) if f.endswith('.png')])
        if not files:
            print("[KLAIDA] Nerasta nuotraukų aplanke assets/neutral")
            return
        
        print(f"[*] Pradedama animacija ({len(files)} kadrų)...")
        while True:
            for f in files:
                img = Image.open(os.path.join(assets_dir, f))
                tzt.show(img)
                # Greitis - gali pareguliuoti (0.02 bus labai greitai, 0.05 normaliai)
                time.sleep(0.04) 
                
    except Exception as e:
        print(f"Klaida: {e}")

if __name__ == "__main__":
    run_robot()
