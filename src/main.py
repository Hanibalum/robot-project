import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# --- APARATŪROS KONFIGŪRACIJA ---
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Pagal tavo Pin -> GPIO žemėlapį:
DC_GPIO  = 24  # Fizinis Pin 18
RST_GPIO = 25  # Fizinis Pin 22
CS_ID    = 0   # Fizinis Pin 24 (CE0)

class XGORobot:
    def __init__(self):
        # 1. EKRANAS: ST7789 TZT 2.0"
        try:
            # SPI inicializacija (port 0, device 0 = Pin 24)
            self.serial_spi = spi(port=0, device=CS_ID, gpio_DC=DC_GPIO, gpio_RST=RST_GPIO)
            
            # Nurodome 320x240, kad biblioteka leistų sukti vaizdą
            self.device = st7789(self.serial_spi, width=320, height=240, rotation=1)
            
            # Labai svarbu TZT ekranams:
            self.device.contrast(255)
            
            self.display_active = True
            print("[OK] Ekranas paruoštas.")
        except Exception as e:
            print(f"[ERROR] Ekranas: {e}")
            self.display_active = False

        # 2. EMOCIJOS
        self.assets_path = "src/assets"
        self.current_emotion = "neutral"
        self.frames = []
        self._load_emotion_frames()

        # 3. AUDIO IR UART
        self.audio = pyaudio.PyAudio()
        self.mic_index = 0 # Card 0
        self.uart_port = '/dev/serial0'

    def _load_emotion_frames(self):
        folder = os.path.join(self.assets_path, self.current_emotion)
        self.frames = []
        try:
            if not os.path.exists(folder): raise FileNotFoundError
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                img = img.resize((320, 240))
                self.frames.append(img)
            print(f"[OK] Užkrauta emocija: {self.current_emotion}")
        except:
            # Jei neranda failų - RYŠKIAI MĖLYNAS testas
            test_img = Image.new("RGB", (320, 240), (0, 0, 255))
            self.frames = [test_img]
            print("[WARN] Emocijos nerastos, rodau mėlyną testą.")

    async def animation_loop(self):
        """Asinhroninis vaizdo rodymas"""
        print("[*] Animacijos ciklas paleistas.")
        while self.display_active:
            for frame in self.frames:
                self.device.display(frame)
                await asyncio.sleep(0.05)

    def _record_audio_sync(self):
        CHUNK, RATE = 1024, 16000 # 16kHz yra stabiliausia
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
        except: return False

    async def uart_task(self):
        try:
            reader, writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            print("[OK] UART ryšys aktyvus.")
            while True:
                writer.write(b'\x00')
                await writer.drain()
                await asyncio.sleep(5)
        except: print("[ERROR] UART nepavyko.")

    async def main_loop(self):
        # Paleidžiame vaizdą ir UART
        asyncio.create_task(self.animation_loop())
        asyncio.create_task(self.uart_task())
        
        while True:
            await asyncio.sleep(15)
            print("[*] Mikrofonas: testas...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
