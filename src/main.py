import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
import st7789
from PIL import Image, ImageDraw

# Sistemos nustatymai
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
BACKLIGHT_PIN = 18 # Dažniausiai Waveshare Nano B apšvietimas čia

class XGORobot:
    def __init__(self):
        # 1. EKRANAS: Nustatymai be rotacijos (FIXED)
        try:
            # Įjungiam apšvietimą fiziškai
            GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
            GPIO.output(BACKLIGHT_PIN, GPIO.HIGH)

            # Inicijuojame 240x320 be jokios vidinės rotacijos
            self.disp = st7789.ST7789(
                port=0,
                cs=1,        # CS7
                dc=24,
                rst=25,
                width=240,   
                height=320,
                rotation=0,  # Paliekam 0, kad nekiltų klaidos
                spi_speed_hz=16000000
            )
            self.disp.begin()
            self.display_active = True
            print("[OK] Ekranas paruoštas (Hardware mode: 0 deg)")
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
        self.uart_writer = None

    def _load_emotion_frames(self):
        """Užkrauna ir pasuka kadrus rankiniu būdu"""
        folder = os.path.join(self.assets_path, self.current_emotion)
        self.frames = []
        try:
            if not os.path.exists(folder): raise FileNotFoundError
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                # --- Rankinis pasukimas ---
                img = img.resize((320, 240)) # Sukuriame gulsčią vaizdą
                img = img.rotate(90, expand=True) # Pasukame, kad tilptų į 240x320 ekraną
                self.frames.append(img)
            print(f"[OK] Užkrauta: {self.current_emotion}")
        except:
            # Jei failų nėra, sukuriam ryškiai ŽALIĄ kadrą testui
            test_img = Image.new("RGB", (320, 240), (0, 255, 0))
            test_img = test_img.rotate(90, expand=True)
            self.frames = [test_img]
            print("[WARN] Emocijos nerastos, rodau žalią testą.")

    async def animation_loop(self):
        """Siunčiame jau pasuktus kadrus"""
        if not self.display_active: return
        while True:
            for frame in self.frames:
                self.disp.display(frame)
                await asyncio.sleep(0.05)

    async def init_uart(self):
        try:
            _, self.uart_writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            print("[OK] UART ryšys paruoštas.")
        except: print("[ERROR] UART nepavyko.")

    def _record_audio_sync(self):
        # Naudojame 48000Hz - tai stabiliausias dažnis šiam mikrofonui
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
            print(f"[ERROR] Audio įrašymas: {e}")
            return False

    async def main_loop(self):
        await self.init_uart()
        asyncio.create_task(self.animation_loop())
        while True:
            await asyncio.sleep(15)
            print("[*] Mikrofonas testuojamas (2s)...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()

