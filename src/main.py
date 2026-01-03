import time
import ST7789
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw

# Pinų konfigūracija pagal tavo Waveshare Nano B
# CS=7 (CE1), DC=24, RST=25
cs_pin = 7
dc_pin = 24
rst_pin = 25
backlight_pin = 18 # Jei valdomas per GPIO

def hard_reset_display():
    """Fizinis ekrano perkrovimas per RST piną"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(rst_pin, GPIO.OUT)
    GPIO.output(rst_pin, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(rst_pin, GPIO.HIGH)
    time.sleep(0.1)

def run_test():
    print("Pradedamas gilus ST7789 testas...")
    hard_reset_display()

    # Inicijuojame ekraną tiesiogiai
    # port=0, cs=1 atitinka /dev/spidev0.1 (CS7)
    disp = ST7789.ST7789(
        port=0,
        cs=1, 
        dc=dc_pin,
        rst=rst_pin,
        width=240,
        height=320,
        rotation=90,
        spi_speed_hz=16000000 # 16MHz yra saugus greitis
    )

    # Pradedame ekrano darbą
    disp.begin()

    # Testas 1: Ryškiai MĖLYNAS ekranas
    print("Siunčiu MĖLYNĄ spalvą...")
    img = Image.new("RGB", (320, 240), (0, 0, 255))
    disp.display(img)
    time.sleep(2)

    # Testas 2: Tekstas ant ekrano
    print("Siunčiu tekstą...")
    img = Image.new("RGB", (320, 240), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((20, 20, 300, 220), outline="red", fill="white")
    draw.text((80, 110), "XGO-CM4: ACTIVE", fill="black")
    disp.display(img)
    print("Testas baigtas. Ar matai tekstą baltame fone?")

if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
