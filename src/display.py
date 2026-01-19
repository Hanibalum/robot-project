import st7789
from PIL import Image
import os
import asyncio
import RPi.GPIO as GPIO
import time

class EvilSonicDisplay:
    def __init__(self, assets_dir="/home/cm4/robot-project/src/assets/"):
        self.assets_dir = assets_dir
        self.current_state = "static"
        self.frames = {}
        self.frame_counter = 0
        
        # --- APARATŪRINIAI PATAISYMAI ---
        # Pinai (pagal tavo schemą)
        self.DC_GPIO = 24
        self.RST_GPIO = 25
        self.CS_DEVICE = 0 # Pin 24 (CE0)

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.RST_GPIO, GPIO.OUT)

        # 1. Fizinis RESET (SVARBU: Išvalo sniegą ir pažadina valdiklį)
        GPIO.output(self.RST_GPIO, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.RST_GPIO, GPIO.HIGH)
        time.sleep(0.1)

        # 2. Inicijuojame ST7789 (Naudojame 0 rotaciją, kad nebūtų klaidų)
        self.disp = st7789.ST7789(
            port=0,
            cs=self.CS_DEVICE,
            dc=self.DC_GPIO,
            rst=self.RST_GPIO,
            width=240,
            height=320,
            rotation=0, # Paliekame 0, kad išvengtume bibliotekos klaidų
            spi_speed_hz=8000000 # 8MHz užtikrina stabilumą be triukšmo
        )
        
        self.disp.begin()
        
        # 3. TZT SPECIFINĖS KOMANDOS (Pažadina vaizdą ir spalvas)
        self.disp.command(0x21) # INVON (Inversion On) - Būtina tavo ekranui
        self.disp.command(0x11) # SLPOUT (Išeiti iš miego)
        self.disp.command(0x29) # DISPON (Įjungti išvedimą)
        
        # Užkrauname assets
        self.load_assets()

    def load_assets(self):
        """Užkrauna PNG kadrus ir juos pasuka 90 laipsnių rankiniu būdu"""
        states = ["static", "speaking", "angry", "laughing", "shook"]
        
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_path if hasattr(self, 'assets_path') else self.assets_dir, state)
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    try:
                        img = Image.open(os.path.join(path, f)).convert("RGB")
                        # --- RANKINIS PASUKIMAS (Apeinam bibliotekos klaidą) ---
                        # Rezaisinam į gulsčią ir pasukam į portretinį ekraną
                        img = img.resize((320, 240))
                        img = img.rotate(90, expand=True)
                        self.frames[state].append(img)
                    except Exception as e:
                        print(f"Klaida kraunant {f}: {e}")
            
            if not self.frames[state]:
                print(f"Warning: Asset folder empty or not found: {path}")
                # Avarinis mėlynas kadras, kad matytume, jog ekranas gyvas
                err_img = Image.new('RGB', (240, 320), color=(0, 0, 255))
                self.frames[state].append(err_img)

    def get_next_frame(self):
        """Išsaugojome JULES sukurtą Ping-Pong logiką"""
        frames = self.frames.get(self.current_state, [])
        if not frames:
            return Image.new('RGB', (240, 320), color=(0, 0, 0))
            
        total_frames = len(frames)
        
        if self.current_state in ["angry", "shook"] and total_frames > 1:
            if self.frame_counter < total_frames:
                idx = self.frame_counter
            else:
                loop_start = total_frames // 2
                loop_len = total_frames - loop_start
                if loop_len > 1:
                    frames_in_loop = self.frame_counter - total_frames
                    cycle_len = (loop_len * 2) - 2
                    pos = frames_in_loop % cycle_len
                    offset = pos if pos < loop_len else cycle_len - pos
                    idx = loop_start + offset
                else:
                    idx = total_frames - 1
        else:
            idx = self.frame_counter % total_frames
            
        return frames[idx]

    async def animate(self):
        """Pagrindinis vaizdo atnaujinimo ciklas"""
        print("[*] Ekrano animacija paleista...")
        while True:
            start_time = asyncio.get_event_loop().time()
            
            img = self.get_next_frame()
            self.disp.display(img)
            
            self.frame_counter += 1
            
            elapsed = asyncio.get_event_loop().time() - start_time
            # 20 FPS (0.05s)
            await asyncio.sleep(max(0.001, 0.05 - elapsed))

    def set_state(self, new_state):
        if new_state in self.frames and new_state != self.current_state:
            print(f"[DISPLAY] Keiciama busena i: {new_state}")
            self.current_state = new_state
            self.frame_counter = 0
