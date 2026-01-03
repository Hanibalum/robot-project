import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# Sistemos nustatymai
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
BACKLIGHT_PIN = 18

class XGORobot:
    def __init__(self):
        # 1. EKRANAS (Naudojame luma.lcd stabilesniam darbui)
        try:
            GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
            GPIO.output(BACKLIGHT_PIN, GPIO.HIGH)

            # Inicijuojame be jokios rotacijos (0 deg), kad nebūtų klaidų
            self.serial_spi = spi(port=0, device=1, gpio_DC=24, gpio_RST=25)
            self.device = st7789(self.serial_spi, width=240, height=320, rotation=0)
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
        self.mic_index = 0
        self.uart_port = '/dev/serial0'

    def _load_emotion_frames(self):
        folder = os.path.join(self.assets_path, self.current_emotion)
        self.frames = []
        try:
            if not os.path.exists(folder): raise FileNotFoundError
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                # Rankinis pasukimas: gulsčias vaizdas (320x240) pasukamas į stovintį (240x320)
                img = img.resize((320, 240))
                img = img.rotate(90, expand=True)
                self.frames.append(img)
            print(f"[OK] Užkrauta emocija: {self.current_emotion}")
        except:
            # Jei neranda failų - RYŠKIAI MĖLYNAS testas
            test_img = Image.new("RGB", (320, 240), (0, 0, 255))
            test_img = test_img.rotate(90, expand=True)
            self.frames = [test_img]
            print("[WARN] Emocijos nerastos, rodau mėlyną testą.")

    async def animation_loop(self):
        """Šis ciklas atsakingas tik už vaizdą"""
        print("[*] Animacijos ciklas paleistas.")
        while self.display_active:
            for frame in self.frames:
                self.device.display(frame)
                await asyncio.sleep(0.05)

    def _record_audio_sync(self):
        CHUNK, RATE = 1024, 48000
        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=RATE, 
                                     input=True, input_device_index=self.mic_index,
                                     frames_per_buffer=CHUNK)
            frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * 2))]
            stream.stop_stream(); stream.close()
            with wave.open("src/test.wav", 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16)); wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            return True
        except Exception as e:
            print(f"[ERROR] Audio: {e}")
            return False

    async def uart_task(self):
        """UART ryšys atskiroje užduotyje, kad nepakibtų visas procesas"""
        try:
            print("[*] Jungiamasi prie UART...")
            reader, writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            print("[OK] UART ryšys aktyvus.")
            while True:
                writer.write(b'\x00')
                await writer.drain()
                await asyncio.sleep(5)
        except Exception as e:
            print(f"[ERROR] UART: {e}")

    async def main_loop(self):
        # SVARBU: Pirmiausia paleidžiame vaizdą!
        asyncio.create_task(self.animation_loop())
        
        # Tada paleidžiame UART
        asyncio.create_task(self.uart_task())
        
        # Pagrindinis darbo ciklas (Audio)
        while True:
            await asyncio.sleep(15)
            print("[*] Mikrofonas testuojamas...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
