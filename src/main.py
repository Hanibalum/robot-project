import time
import os
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import st7789

# --- TAVO PATVIRTINTI KONTAKTAI ---
# Pin 24 = GPIO 8 (CE0) -> cs=0
# Pin 18 = GPIO 24 (DC)
# Pin 22 = GPIO 25 (RST)
DC_GPIO  = 24  
RST_GPIO = 25  
CS_DEVICE = 0  

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def final_rescue():
    print("[*] PRADEDAMAS AGRESYVUS EKRANO ATGAIVINIMAS...")
    
    # 1. Fizinis RESET (SVARBU: išvalo visus sniegus ir pakibimus)
    GPIO.setup(RST_GPIO, GPIO.OUT)
    GPIO.output(RST_GPIO, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(RST_GPIO, GPIO.HIGH)
    time.sleep(0.5)

    try:
        # 2. Inicijuojame įrenginį be rotacijos (0 laipsnių), kad nekiltų klaidų
        disp = st7789.ST7789(
            port=0, 
            cs=CS_DEVICE, 
            dc=DC_GPIO, 
            rst=RST_GPIO,
            width=240, 
            height=320, 
            rotation=0, 
            spi_speed_hz=4000000 # 4MHz - labai lėtai, bet užtikrintai
        )
        disp.begin()
        
        # 3. TIESIOGINĖ KOMANDA INVERSIJAI (Pažadina spalvas TZT ekranuose)
        # Jei 'set_inversion' nebuvo, ši komanda suveiks 100%
        disp.command(0x21) 

        # 4. TESTINIS VAIZDAS: Ryškiai ŽALIAS ekranas
        # Tai parodys, ar SPI ryšys veikia
        print("[*] Siunčiu ŽALIĄ spalvą...")
        test_img = Image.new("RGB", (240, 320), (0, 255, 0))
        draw = ImageDraw.Draw(test_img)
        draw.text((40, 150), "SPI RYŠYS: OK", fill=(0, 0, 0))
        disp.display(test_img)
        
        print("[SĖKMĖ] Jei ekranas ŽALIAS – sistema paruošta gynimui.")

    except Exception as e:
        print(f"[KLAIDA] Nepavyko: {e}")

if __name__ == "__main__":
    final_rescue()
