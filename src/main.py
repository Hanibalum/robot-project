import time
import os
import RPi.GPIO as GPIO
import st7789
from PIL import Image, ImageDraw

# --- KONFIGŪRACIJA (Griežtai pagal tavo fizinius laidus) ---
# Pin 24 = GPIO 8 (CE0) -> cs=0
# Pin 18 = GPIO 24 (DC)
# Pin 22 = GPIO 25 (RST)
DC_GPIO = 24
RST_GPIO = 25
CS_DEVICE = 0  

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def run_rescue():
    print("[*] PRADĖTAS EKRANO ATGAIVINIMAS...")
    
    # 1. Inicijuojame įrenginį
    # width/height sukeisti, kad tiktų TZT moduliui
    disp = st7789.ST7789(
        port=0,
        cs=CS_DEVICE,
        dc=DC_GPIO,
        rst=RST_GPIO,
        width=320, 
        height=240,
        rotation=90,
        spi_speed_hz=4000000 # 4MHz (labai lėtai, bet stabiliai)
    )
    disp.begin()
    disp.set_inversion(True) # SVARBU: TZT ekranams be šito bus tik triukšmas

    # 2. TESTAS: Užpildome ekraną raudonai, kad matytume ar veikia
    print("[*] Siunčiu raudoną spalvą...")
    red_img = Image.new("RGB", (320, 240), (255, 0, 0))
    disp.display(red_img)
    time.sleep(2)

    # 3. KRAUNAME EMOCIJAS (Neutral)
    assets_path = os.path.join(os.path.dirname(__file__), "assets", "neutral")
    print(f"[*] Ieškau emocijų čia: {assets_path}")
    
    try:
        files = sorted([f for f in os.listdir(assets_path) if f.endswith('.png')])
        frames = [Image.open(os.path.join(assets_path, f)).convert("RGB").resize((320, 240)) for f in files]
        print(f"[OK] Užkrauta {len(frames)} kadrų.")
    except:
        print("[KLAIDA] Nerasti assets. Piešiu avarines akis.")
        err_img = Image.new("RGB", (320, 240), (0, 0, 0))
        d = ImageDraw.Draw(err_img)
        d.ellipse((80, 80, 120, 160), fill="red")
        d.ellipse((200, 80, 240, 160), fill="red")
        frames = [err_img]

    # 4. PAGRINDINIS CIKLAS (Be asinhroniškumo, kad niekas nestrigtų)
    print("[OK] Animacija paleista!")
    while True:
        for frame in frames:
            disp.display(frame)
            time.sleep(0.05)

if __name__ == "__main__":
    run_rescue()
