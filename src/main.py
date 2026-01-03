import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
import st7789 # Naudojame mažosiomis raidėmis, kaip prašė sistema
from PIL import Image, ImageDraw

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class XGORobot:
    def __init__(self):
        # --- EKRANO KONFIGŪRACIJA (Fiksuota rotacija) ---
        try:
            # Sukeičiame 320 su 240, kad veiktų rotation=90
            self.disp = st7789.ST7789(
                port=0,
                cs=1, # CS7 yra spidev0.1
                dc=24,
                rst=25,
                width=320, 
                height=240,
                rotation=90, 
                spi_speed_hz=16000000
            )
            self.disp.begin()
            self.display_active = True
            print("[OK] Ekranas inicijuotas sėkmingai.")
        except Exception as e:
            print(f"[ERROR] Ekranas nepasileido: {e}")
            self.display_active = False

        # --- EMOCIJOS ---
        self.assets_path = "src/assets"
        self.current_emotion = "neutral"
        self.frames = []
        self._load_emotion_frames()

        # --- AUDIO IR UART ---
        self.audio = pyaudio.PyAudio()
        self.mic_index = 0 # Tavo Card 0
        self.uart_port = '/dev/serial0'
        self.uart_writer = None

    def _load_emotion_frames(self):
        folder = os.path.join(self.assets_path, self.current_emotion)
        self.frames = []
        try:
            # Užkrauname tik .png failus
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                img = img.resize((320, 240))
                self.frames.append(img)
            print(f"[OK] Užkrauta emocija '{self.current_emotion}': {len(self.frames)} kadrai.")
        except Exception as e:
            print(f"[ERROR] Emocijų krovimas: {e}")
            # Atsarginis vaizdas (Mėlynas ekranas su užrašu), kad žinotume, jog ekranas veikia
            err_img = Image.new("RGB", (320, 240), (0, 0, 255))
            draw = ImageDraw.Draw(err_img)
            draw.text((80, 110), "EKRANAS VEIKIA", fill="white")
            self.frames = [err_img]

    async def animation_loop(self):
        """Suka animaciją fone"""
        print("[*] Animacijos ciklas paleistas.")
        while self.display_active:
            for frame in self.frames:
                self.disp.display(frame)
                await asyncio.sleep(0.06)

    async def init_uart(self):
        try:
            _, self.uart_writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            print(f"[OK] UART ryšys paruoštas.")
        except:
            print(f"[ERROR] UART nepavyko prisijungti.")

    def _record_audio_sync(self):
        """Garso įrašymas 16000Hz dažniu"""
        CHUNK, RATE = 1024, 16000
        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=RATE, 
                                     input=True, input_device_index=self.mic_index,
                                     frames_per_buffer=CHUNK)
            frames = []
            for _ in range(0, int(RATE / CHUNK * 3)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            stream.stop_stream()
            stream.close()
            with wave.open("src/test.wav", 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16)); wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            return True
        except Exception as e:
            print(f"[ERROR] Audio įrašymas: {e}")
            return False

    async def main_loop(self):
        await self.init_uart()
        # Paleidžiame animaciją
        asyncio.create_task(self.animation_loop())
        
        while True:
            await asyncio.sleep(10)
            print("[*] Įrašinėjamas bandomasis garsas...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)
            print("[OK] Įrašas baigtas.")

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
