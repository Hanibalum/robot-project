import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
import st7789
from PIL import Image, ImageDraw

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class XGORobot:
    def __init__(self):
        # --- EKRANAS: Naudojame nurodytus pimus ir natyvią rezoliuciją ---
        try:
            self.disp = st7789.ST7789(
                port=0,
                cs=1,        # CS7 (CE1)
                dc=24,       # DC
                rst=25,      # Reset
                width=240,   # Natyvus plotis
                height=320,  # Natyvus aukštis
                rotation=90, # Pasukimas (Dabar biblioteka leis)
                spi_speed_hz=16000000
            )
            self.disp.begin()
            self.display_active = True
            print("[OK] Ekranas inicijuotas.")
        except Exception as e:
            print(f"[ERROR] Ekranas: {e}")
            self.display_active = False

        # --- EMOCIJOS ---
        self.assets_path = "src/assets"
        self.current_emotion = "neutral"
        self.frames = []
        self._load_emotion_frames()

        # --- AUDIO IR UART ---
        self.audio = pyaudio.PyAudio()
        self.mic_index = 0
        self.uart_port = '/dev/serial0'
        self.uart_writer = None

    def _load_emotion_frames(self):
        folder = os.path.join(self.assets_path, self.current_emotion)
        self.frames = []
        try:
            if not os.path.exists(folder): raise FileNotFoundError
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                # Kadangi ekranas pasuktas 90 laipsnių, piešiame ant 320x240 drobės
                img = img.resize((320, 240))
                self.frames.append(img)
        except:
            # Jei failų nėra, sukuriam ryškų kadrą testui
            test_img = Image.new("RGB", (320, 240), (0, 255, 0)) # Žalia spalva
            draw = ImageDraw.Draw(test_img)
            draw.text((100, 110), "EKRANAS GYVAS", fill="black")
            self.frames = [test_img]

    async def animation_loop(self):
        while self.display_active:
            for frame in self.frames:
                self.disp.display(frame)
                await asyncio.sleep(0.06)

    async def init_uart(self):
        try:
            _, self.uart_writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            print("[OK] UART ryšys paruoštas.")
        except: print("[ERROR] UART nepavyko.")

    def _record_audio_sync(self):
        # ICS-43434 dažniausiai reikalauja 48000Hz (jei 16000 netiko)
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
            print(f"[ERROR] Mikrofonas: {e}")
            return False

    async def main_loop(self):
        await self.init_uart()
        asyncio.create_task(self.animation_loop())
        while True:
            await asyncio.sleep(10)
            print("[*] Įrašinėju 2s garsą...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
