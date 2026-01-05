import RPi.GPIO as GPIO
import time
import spidev
from PIL import Image

# --- TAVO PATIKRINTI PINAI (Fiziniai -> GPIO) ---
# Pin 24 (CS)  -> GPIO 8 (CE0)
# Pin 18 (DC)  -> GPIO 24
# Pin 22 (RST) -> GPIO 25
DC = 24
RST = 25

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([DC, RST], GPIO.OUT)

class TZT_Display:
    def __init__(self):
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 40000000 # 40MHz
        self.spi.mode = 0b11 # Mode 3 dažnai padeda TZT ekranams

    def write_cmd(self, cmd):
        GPIO.output(DC, GPIO.LOW)
        self.spi.writebytes([cmd])

    def write_data(self, data):
        GPIO.output(DC, GPIO.HIGH)
        if isinstance(data, int): data = [data]
        self.spi.writebytes(data)

    def init(self):
        # Fizinis Reset
        GPIO.output(RST, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST, GPIO.HIGH)
        time.sleep(0.1)

        self.write_cmd(0x01) # Software reset
        time.sleep(0.15)
        self.write_cmd(0x11) # Sleep out
        time.sleep(0.1)
        
        # TZT 2.0" specifiniai spalvų ir atminties nustatymai
        self.write_cmd(0x3A) ; self.write_data(0x05) # 16-bit color
        self.write_cmd(0x36) ; self.write_data(0x00) # MADCTL
        self.write_cmd(0x21) # Inversion ON
        self.write_cmd(0x29) # Display ON
        print("[OK] Ekranas pažadintas rankiniu būdu.")

    def show(self, image):
        # Paruošiam vaizdą išvedimui
        img = image.resize((240, 320)).rotate(90, expand=True)
        pixel_data = []
        # Konvertuojame į RGB565 (2 baitai per pikselį)
        rgb888 = img.convert("RGB")
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = rgb888.getpixel((x, y))
                color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                pixel_data.append(color >> 8)
                pixel_data.append(color & 0xFF)
        
        # Siunčiame į RAM
        self.write_cmd(0x2A) # Column address
        self.write_data([0, 0, 0, 239])
        self.write_cmd(0x2B) # Row address
        self.write_data([0, 0, 1, 63])
        self.write_cmd(0x2C) # Memory write
        
        # Siunčiame dalimis, kad spidev neužspringtų
        chunk_size = 4096
        GPIO.output(DC, GPIO.HIGH)
        for i in range(0, len(pixel_data), chunk_size):
            self.spi.writebytes(pixel_data[i:i+chunk_size])

if __name__ == "__main__":
    try:
        tzt = TZT_Display()
        tzt.init()
        # Sukuriam bandomąjį kadrą (MĖLYNAS)
        img = Image.new("RGB", (320, 240), (0, 0, 255))
        print("[*] Siunčiu MĖLYNĄ spalvą...")
        tzt.show(img)
        print("[SĖKMĖ] Jei matai mėlyną spalvą - ekranas veikia!")
    except KeyboardInterrupt:
        GPIO.cleanup()
