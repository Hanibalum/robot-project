import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from itertools import cycle

GPIO.setwarnings(False)

class XGORobot:
    def __init__(self):
        # 1. Ekranas (ST7789)
        try:
            self.serial_spi = spi(port=0, device=1, gpio_DC=24, gpio_RST=25)
            self.device = st7789(self.serial_spi, width=240, height=320, rotation=0)
            self.display_active = True
        except Exception as e:
            print(f"[ERROR] Ekranas: {e}")
            self.display_active = False

        # 2. Emocijų valdymas
        self.assets_path = "src/assets"
        self.current_emotion = "neutral"
        self.frames = []
        self._load_emotion_frames()

        # 3. UART ir Audio
        self.uart_port = '/dev/serial0'
        self.uart_writer = None
        self.audio = pyaudio.PyAudio()
        self.mic_index = 0 

    def _load_emotion_frames(self):
        """Užkrauna visus .png failus iš pasirinktos emocijos aplanko"""
        folder = os.path.join(self.assets_path, self.current_emotion)
        self.frames = []
        try:
            # Surikiuojame failus (0.png, 1.png...), kad animacija būtų teisinga
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                img = img.resize((240, 320))
                self.frames.append(img)
            print(f"[OK] Užkrauta emocija: {self.current_emotion} ({len(self.frames)} kadrai)")
        except Exception as e:
            print(f"[ERROR] Nepavyko užkrauti emocijos {self.current_emotion}: {e}")
            # Atsarginis juodas rėmelis, jei neranda failų
            self.frames = [Image.new("RGB", (240, 320), "black")]

    def set_emotion(self, emotion_name):
        """Pakeičia emociją ir užkrauna jos kadrus"""
        if self.current_emotion != emotion_name:
            self.current_emotion = emotion_name
            self._load_emotion_frames()

    async def animation_loop(self):
        """Nuolatinis animacijos rodymas fone (neblokuojantis)"""
        while self.display_active:
            for frame in self.frames:
                self.device.display(frame)
                # Kadrų greitis (mažesnis skaičius = greitesnė animacija)
                await asyncio.sleep(0.08) 
            await asyncio.sleep(0.1)

    async def init_uart(self):
        try:
            _, self.uart_writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            self.uart_writer.write(b'\x00')
            await self.uart_writer.drain()
            print("[OK] UART paruoštas.")
        except:
            print("[ERROR] UART nepavyko.")

    def _record_audio_sync(self):
        CHUNK, RATE = 1024, 16000
        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                                     input=True, input_device_index=self.mic_index,
                                     frames_per_buffer=CHUNK)
            frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * 3))]
            stream.stop_stream(); stream.close()
            with wave.open("src/test.wav", 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16)); wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            return True
        except: return False

    async def main_loop(self):
        await self.init_uart()
        
        # Paleidžiame animaciją kaip atskirą užduotį
        asyncio.create_task(self.animation_loop())
        
        while True:
            # Robotas būna ramus
            self.set_emotion("neutral")
            await asyncio.sleep(8)
            
            # Robotas pradeda klausytis
            print("[*] Klausausi...")
            self.set_emotion("excited") # Pakeičiame akis į "excited" įrašymo metu
            
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)
            
            # Po įrašymo parodome, kad pabaigėme
            self.set_emotion("happy")
            await asyncio.sleep(2)

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nSustabdyta.")
