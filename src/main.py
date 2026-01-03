import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
import time
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- KONFIGŪRACIJA (Griežtai pagal tavo pinuose) ---
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
DC_PIN = 24
RST_PIN = 25
BL_PIN = 18  # Backlight
CS_PIN = 7   # Tai yra CE1 (device 1)

class XGORobot:
    def __init__(self):
        self.display_active = False
        self._init_hardware_display()
        
        # Emocijų kelias
        self.assets_path = "src/assets"
        self.current_emotion = "neutral"
        self.frames = []
        self._load_emotion_frames()

        # Audio/UART nustatymai
        self.audio = pyaudio.PyAudio()
        self.mic_index = 0
        self.uart_port = '/dev/serial0'

    def _init_hardware_display(self):
        """Fiziškai pažadiname ST7789 valdiklį"""
        try:
            print("[*] Vykdomas aparatūrinis ekrano RESET...")
            GPIO.setup([DC_PIN, RST_PIN, BL_PIN], GPIO.OUT)
            
            # Fizinis RESET ciklas
            GPIO.output(RST_PIN, GPIO.HIGH)
            time.sleep(0.05)
            GPIO.output(RST_PIN, GPIO.LOW)
            time.sleep(0.1)
            GPIO.output(RST_PIN, GPIO.HIGH)
            time.sleep(0.1)
            
            # Įjungiam apšvietimą
            GPIO.output(BL_PIN, GPIO.HIGH)

            # SPI inicializacija: port=0, device=1 (CS7)
            # baudrate sumažintas iki 4MHz - tai turi veikti net su prasčiausiais laidais
            self.serial_spi = spi(port=0, device=1, gpio_DC=DC_PIN, gpio_RST=RST_PIN, baudrate=4000000)
            
            # Sukuriame įrenginį. rotation=1 (90 laipsnių)
            self.device = st7789(self.serial_spi, width=240, height=320, rotation=1)
            
            self.display_active = True
            print("[OK] Ekranas pažadintas sėkmingai.")
        except Exception as e:
            print(f"[ERROR] Ekranas: {e}")

    def _load_emotion_frames(self):
        folder = os.path.join(self.assets_path, self.current_emotion)
        self.frames = []
        try:
            # Surenkame kadrus. Kadangi rotation=1, ekranas dabar yra 320x240
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                img = img.resize((320, 240))
                self.frames.append(img)
            print(f"[OK] Užkrauta emocija: {self.current_emotion}")
        except:
            # Jei failų nėra - RYŠKIAI BALTAS ekranas testui
            print("[WARN] Emocijos nerastos. Naudojamas baltas testinis vaizdas.")
            test_img = Image.new("RGB", (320, 240), "white")
            draw = ImageDraw.Draw(test_img)
            draw.text((100, 110), "EKRANAS GYVAS", fill="black")
            self.frames = [test_img]

    async def animation_loop(self):
        """Asinhroninis vaizdo atnaujinimas"""
        print("[*] Pradedamas vaizdo išvedimas...")
        while self.display_active:
            for frame in self.frames:
                self.device.display(frame)
                await asyncio.sleep(0.04)

    def _record_audio_sync(self):
        """Saugaus dažnio garso įrašymas"""
        # Pakeista į 16000, nes tai stabiliausias dažnis ICS-43434 mikrofonui ant CM4
        CHUNK, RATE = 1024, 16000
        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=RATE, 
                                     input=True, input_device_index=self.mic_index,
                                     frames_per_buffer=CHUNK)
            frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * 2))]
            stream.stop_stream(); stream.close()
            with wave.open("src/test.wav", 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16)); wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            print("[OK] Garsas įrašytas į src/test.wav")
            return True
        except Exception as e:
            print(f"[ERROR] Audio: {e}")
            return False

    async def uart_task(self):
        """UART ryšys su ESP32"""
        try:
            reader, writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            print("[OK] UART ryšys paruoštas.")
            while True:
                writer.write(b'\x00') # Gyvybės signalas važiuoklei
                await writer.drain()
                await asyncio.sleep(5)
        except:
            print("[ERROR] UART nepavyko.")

    async def main_loop(self):
        # 1. Paleidžiame animaciją
        asyncio.create_task(self.animation_loop())
        # 2. Paleidžiame UART
        asyncio.create_task(self.uart_task())
        
        # 3. Pagrindinis ciklas mikrofonui
        while True:
            await asyncio.sleep(15)
            print("[*] Mikrofonas: įrašinėju 2s...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nSistemos darbas nutrauktas.")
