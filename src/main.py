import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
import ST7789
from PIL import Image, ImageDraw

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class XGORobot:
    def __init__(self):
        # --- Ekrano konfigūracija ---
        # CS:7 (port 0, device 1), DC:24, RST:25
        try:
            self.disp = ST7789.ST7789(
                port=0,
                cs=1, 
                dc=24,
                rst=25,
                width=240,
                height=320,
                rotation=90,
                spi_speed_hz=16000000
            )
            self.disp.begin()
            self.display_active = True
            print("[OK] Ekranas inicijuotas su ST7789 biblioteka.")
        except Exception as e:
            print(f"[ERROR] Ekranas: {e}")
            self.display_active = False

        # --- Emocijų kelias ---
        self.assets_path = "src/assets"
        self.current_emotion = "neutral"
        self.frames = []
        self._load_emotion_frames()

        # --- UART ir Audio ---
        self.uart_port = '/dev/serial0'
        self.uart_writer = None
        self.audio = pyaudio.PyAudio()

    def _load_emotion_frames(self):
        folder = os.path.join(self.assets_path, self.current_emotion)
        self.frames = []
        try:
            # Surenkam visus .png failus iš aplanko
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            if not files:
                raise FileNotFoundError("Aplankas tuscias")
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                img = img.resize((320, 240)) # Sukeitėm vietom dėl rotacijos
                self.frames.append(img)
            print(f"[OK] Užkrauta: {self.current_emotion} ({len(self.frames)} kadrai)")
        except Exception as e:
            print(f"[ERROR] Emocija: {e}")
            # Jei neranda failų, sukuriam raudoną kadrą testui
            err_img = Image.new("RGB", (320, 240), "red")
            self.frames = [err_img]

    async def animation_loop(self):
        """Šis ciklas suka animaciją"""
        while self.display_active:
            for frame in self.frames:
                self.disp.display(frame)
                await asyncio.sleep(0.05) # Greitis

    async def init_uart(self):
        try:
            _, self.uart_writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            print("[OK] UART paruoštas.")
        except:
            print("[ERROR] UART nepavyko.")

    def _record_audio_sync(self):
        CHUNK, RATE = 1024, 16000
        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
            frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * 3))]
            stream.stop_stream(); stream.close()
            with wave.open("src/test.wav", 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16)); wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            return True
        except: return False

    async def main_loop(self):
        await self.init_uart()
        # Paleidžiam animaciją fone
        asyncio.create_task(self.animation_loop())
        
        while True:
            await asyncio.sleep(15)
            print("[*] Įrašinėju garsą...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)
            print("[OK] Įrašas baigtas.")

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
