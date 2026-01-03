import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
import st7789 # Naudojame šią biblioteką tiesioginiam valdymui
from PIL import Image, ImageDraw

# Sistemos nustatymai
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
BACKLIGHT_PIN = 18

class XGORobot:
    def __init__(self):
        # 1. EKRANAS (Su specifiniais TZT 2.0" nustatymais)
        try:
            # Įjungiam apšvietimą
            GPIO.setup(BACKLIGHT_PIN, GPIO.OUT)
            GPIO.output(BACKLIGHT_PIN, GPIO.HIGH)

            # Inicijuojame su 'offset' pataisymais
            # Dauguma 2.0" ST7789 modulių reikalauja šių nustatymų:
            self.disp = st7789.ST7789(
                port=0,
                cs=1,         # CS7 (CE1)
                dc=24,
                rst=25,
                width=240,
                height=320,
                rotation=90,  # Bandome vėl 90, jei mes klaidą - pakeisim į 0
                spi_speed_hz=40000000 # Padidintas greitis sklandumui
            )
            
            # TZT modulių specifika: rankinis inicijavimas
            self.disp.begin()
            
            # Jei vaizdas vis tiek juodas, po .begin() pridedame spalvų inversiją
            # self.disp.set_inversion(True) 
            
            self.display_active = True
            print("[OK] Ekranas inicijuotas.")
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
            # Surenkame .png failus
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                # Kadangi ekranas 240x320 pasuktas 90 laipsnių, piešiame 320x240
                img = img.resize((320, 240))
                self.frames.append(img)
            print(f"[OK] Užkrauta emocija: {self.current_emotion}")
        except:
            # Jei neranda failų - TESTINIS vaizdas, kad matytume ar ekranas veikia
            test_img = Image.new("RGB", (320, 240), (255, 0, 0)) # RAUDONA
            draw = ImageDraw.Draw(test_img)
            draw.text((100, 110), "TEST: EKRANAS OK", fill="white")
            self.frames = [test_img]
            print("[WARN] Emocijos nerastos, rodau raudoną testą.")

    async def animation_loop(self):
        print("[*] Animacijos ciklas paleistas.")
        while self.display_active:
            for frame in self.frames:
                self.disp.display(frame)
                await asyncio.sleep(0.04) # 25 FPS

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
            print("[OK] Garsas įrašytas.")
            return True
        except Exception as e:
            print(f"[ERROR] Audio: {e}")
            return False

    async def uart_task(self):
        try:
            reader, writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            print("[OK] UART ryšys aktyvus.")
            while True:
                writer.write(b'\x00')
                await writer.drain()
                await asyncio.sleep(5)
        except Exception as e:
            print(f"[ERROR] UART: {e}")

    async def main_loop(self):
        asyncio.create_task(self.animation_loop())
        asyncio.create_task(self.uart_task())
        while True:
            await asyncio.sleep(20)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
