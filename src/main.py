import asyncio
import os
import time
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
import st7789 as st7789_lib
from google import genai

# --- APARATŪRA (Tavo fiziniai pinai) ---
DC_GPIO  = 24  # Pin 18
RST_GPIO = 25  # Pin 22
CS_DEVICE = 0  # Pin 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# --- DI RAKTO KROVIMAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def get_key():
    try:
        with open(os.path.join(BASE_DIR, "secrets.txt"), "r") as f:
            return f.read().strip()
    except: return None

client = genai.Client(api_key=get_key()) if get_key() else None

class XGORobotRescue:
    def __init__(self):
        self.display_active = False
        self.last_ai_text = ""
        self.frames = []
        self.assets_path = os.path.join(BASE_DIR, "assets")

        # 1. EKRANO INICIJAVIMAS (Be vidinės rotacijos, kad nekiltų klaidos)
        try:
            self.disp = st7789_lib.ST7789(
                port=0, cs=CS_DEVICE, dc=DC_GPIO, rst=RST_GPIO,
                width=240, height=320, rotation=0, # Rotation 0, kad nemestų klaidos
                spi_speed_hz=8000000
            )
            self.disp.begin()
            self.display_active = True
            print("[OK] Ekranas inicijuotas.")
        except Exception as e:
            print(f"[FAIL] Ekranas: {e}")

        self._load_emotion("neutral")

    def _load_emotion(self, emotion):
        path = os.path.join(self.assets_path, emotion)
        try:
            files = sorted([f for f in os.listdir(path) if f.endswith('.png')])
            # ČIA ĮVYKSTA STEBUKLAS: Pasukame nuotraukas patys per PIL
            new_frames = []
            for f in files:
                img = Image.open(os.path.join(path, f)).convert("RGB")
                img = img.resize((320, 240)) # Gulsčias dydis
                img = img.rotate(90, expand=True) # Pasukame 90 laipsnių rankiniu būdu
                new_frames.append(img)
            self.frames = new_frames
            print(f"[OK] Užkrauta: {emotion}")
        except:
            # Jei assets nėra, nupiešiam avarines akis
            img = Image.new("RGB", (320, 240), (0, 0, 0))
            d = ImageDraw.Draw(img)
            d.ellipse((80, 80, 120, 160), fill="red")
            d.ellipse((200, 80, 240, 160), fill="red")
            img = img.rotate(90, expand=True)
            self.frames = [img]

    async def animation_loop(self):
        """Šis ciklas suka animaciją"""
        while self.display_active:
            for frame in list(self.frames):
                # Piešiame kadrą. Jei šone balta juosta, čia pridedami poslinkiai.
                # Šiuo metodu vaizdas turi būti per visą ekraną.
                self.disp.display(frame)
                await asyncio.sleep(0.05)

    async def ask_gemini(self):
        if not client: return
        self.last_ai_text = "KLAUSAUSI..."
        await asyncio.sleep(3)
        self.last_ai_text = "MASTAU..."
        try:
            res = await asyncio.to_thread(client.models.generate_content, 
                                          model="gemini-1.5-flash", 
                                          contents="Atsakyk trumpai, piktokai lietuviskai.")
            self.last_ai_text = res.text.upper()
            await asyncio.sleep(7)
            self.last_ai_text = ""
        except: self.last_ai_text = "DI KLAIDA"

    async def main_loop(self):
        # Paleidžiame vaizdą
        asyncio.create_task(self.animation_loop())
        print("[SISTEMA] Viskas veikia. Gynimui paruosta.")
        while True:
            await asyncio.sleep(20)
            await self.ask_gemini()

if __name__ == "__main__":
    robot = XGORobotRescue()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
