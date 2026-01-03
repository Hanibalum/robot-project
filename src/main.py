import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- KONFIGŪRACIJA ---
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
BACKLIGHT_PIN = 18
DC_PIN = 24
RST_PIN = 25

class XGORobot:
    def __init__(self):
        # 1. EKRANAS (Naudojame luma.lcd su priverstiniu įjungimu)
        try:
            GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
            GPIO.output(BACKLIGHT_PIN, GPIO.HIGH) # Įjungiam apšvietimą

            # Inicijuojame SPI ryšį (port 0, device 1 = CS7/CE1)
            self.serial_spi = spi(port=0, device=1, gpio_DC=DC_PIN, gpio_RST=RST_PIN)
            
            # GMT020-02 (ST7789) nustatymai. 
            # rotation=1 reiškia 90 laipsnių (landscape)
            self.device = st7789(self.serial_spi, width=240, height=320, rotation=1)
            
            self.display_active = True
            print("[OK] Ekranas inicijuotas su luma.lcd")
        except Exception as e:
            print(f"[ERROR] Ekranas: {e}")
            self.display_active = False

        # 2. EMOCIJOS (Assets kelias)
        self.assets_path = "src/assets"
        self.current_emotion = "neutral"
        self.frames = []
        self._load_emotion_frames()

        # 3. AUDIO IR UART
        self.audio = pyaudio.PyAudio()
        self.mic_index = 0 # Tavo Card 0
        self.uart_port = '/dev/serial0'

    def _load_emotion_frames(self):
        folder = os.path.join(self.assets_path, self.current_emotion)
        self.frames = []
        try:
            if not os.path.exists(folder): raise FileNotFoundError
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                # Kadangi naudojame rotation=1 (320x240), resize'inam atitinkamai
                img = img.resize((320, 240))
                self.frames.append(img)
            print(f"[OK] Užkrauta emocija: {self.current_emotion}")
        except:
            # Atsarginis vaizdas (RYŠKIAI RAUDONAS), kad matytume, jog ekranas gyvas
            test_img = Image.new("RGB", (320, 240), (255, 0, 0))
            draw = ImageDraw.Draw(test_img)
            draw.text((100, 110), "TEST: EKRANAS OK", fill="white")
            self.frames = [test_img]
            print("[WARN] Emocijos nerastos, rodau raudoną testą.")

    async def animation_loop(self):
        """Siunčiame kadrus į ekraną"""
        print("[*] Animacijos ciklas paleistas.")
        while self.display_active:
            for frame in self.frames:
                self.device.display(frame)
                await asyncio.sleep(0.04) # Greitis ~25 FPS

    def _record_audio_sync(self):
        CHUNK, RATE = 1024, 48000 # 48kHz dažniausiai veikia su ICS-43434
        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=RATE, 
                                     input=True, input_device_index=self.mic_index,
                                     frames_per_buffer=CHUNK)
            frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * 2))]
            stream.stop_stream(); stream.close()
            with wave.open("src/test.wav", 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16)); wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            print("[OK] Garsas įrašytas.")
            return True
        except Exception as e:
            print(f"[ERROR] Audio: {e}")
            return False

    async def main_loop(self):
        # Paleidžiame vaizdą ir kitas užduotis
        asyncio.create_task(self.animation_loop())
        
        while True:
            # Kas 20 sekundžių testuojame mikrofoną
            await asyncio.sleep(20)
            print("[*] Mikrofonas testuojamas...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nSustabdyta.")
