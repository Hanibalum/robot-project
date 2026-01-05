import time
import os
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import st7789

# --- TIKSLŪS KONTAKTAI ---
DC_GPIO  = 24  # Pin 18
RST_GPIO = 25  # Pin 22
CS_DEVICE = 0  # Pin 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def final_test():
    print("[*] PRADEDAMAS AGRESYVUS EKRANO TESTAS...")
    
    # 1. Fizinis RESET
    GPIO.setup(RST_GPIO, GPIO.OUT)
    GPIO.output(RST_GPIO, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(RST_GPIO, GPIO.HIGH)
    time.sleep(0.5)

    try:
        # 2. Inicijuojame be jokių pribumbasų
        disp = st7789.ST7789(
            port=0, cs=CS_DEVICE, dc=DC_GPIO, rst=RST_GPIO,
            width=240, height=320, rotation=0,
            spi_speed_hz=4000000 # 4MHz (labai saugu)
        )
        disp.begin()
        disp.set_inversion(True)

        # 3. TESTAS: NUSPALVINAME EKRANĄ RYŠKIAI RAUDONAI
        # Tai parodys, ar valdiklis reaguoja į komandas
        print("[*] SIUNČIU RAUDONĄ SPALVĄ...")
        red_img = Image.new("RGB", (240, 320), (255, 0, 0))
        disp.display(red_img)
        
        time.sleep(3)
        
        # 4. TESTAS: NUSPALVINAME BALTAI
        print("[*] SIUNČIU BALTĄ SPALVĄ...")
        white_img = Image.new("RGB", (240, 320), (255, 255, 255))
        disp.display(white_img)
        
        print("[SĖKMĖ] Jei matai spalvas - SPI veikia. Jei ne - patikrink Pin 18 (DC).")

    except Exception as e:
        print(f"[KLAIDA] Nepavyko: {e}")

if __name__ == "__main__":
    final_test()
