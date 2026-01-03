import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
import os
import st7789
from PIL import Image, ImageDraw

# --- APARATŪROS KONFIGŪRACIJA ---
# Pagal tavo Pin -> GPIO suderinimą
DC_PIN  = 24  # Pin 18
RST_PIN = 25  # Pin 22
CS_DEVICE = 0 # Pin 24 (GPIO 8 yra CE0)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

class XGORobot:
    def __init__(self):
        # 1. EKRANAS: ST7789 TZT 2.0" setupas
        try:
            # Naudojame port=0, cs=0 (atitinka tavo Pin 24)
            self.disp = st7789.ST7789(
                port=0,
                cs=CS_DEVICE, 
                dc=DC_PIN,
                rst=RST_PIN,
                width=240,   
                height=320,
                rotation=90, # Gulsčias režimas (320x240)
                spi_speed_hz=40000000
            )
            self.disp.begin()
            # TZT ekranams dažnai reikia apversti spalvas
            self.disp.set_inversion(True)
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
        self.mic_index = 0 # Tavo Card 0 iš arecord -l
        self.uart_port = '/dev/serial0'

    def _load_emotion_frames(self):
        folder = os.path.join(self.assets_path, self.current_emotion)
        self.frames = []
        try:
            if not os.path.exists(folder): raise FileNotFoundError
            files = sorted([f for f in os.listdir(folder) if f.endswith('.png')])
            for f in files:
                img = Image.open(os.path.join(folder, f)).convert("RGB")
                # Kadangi ekranas dabar 320x240 (dėl rotation=90)
                img = img.resize((320, 240))
                self.frames.append(img)
            print(f"[OK] Užkrauta emocija: {self.current_emotion}")
        except:
            # Jei neranda failų - RYŠKIAI ŽALIAS testas
            test_img = Image.new("RGB", (320, 240), (0, 255, 0))
            self.frames = [test_img]
            print("[WARN] Emocijų failai nerasti, rodomas testinis vaizdas.")

    async def animation_loop(self):
        """Nuolatinis vaizdo atnaujinimas"""
        print("[*] Vaizdo išvedimas aktyvuotas.")
        while self.display_active:
            for frame in self.frames:
                self.disp.display(frame)
                await asyncio.sleep(0.05) # ~20 FPS

    def _record_audio_sync(self):
        """Garso įrašymas 16000Hz (stabiliausias CM4/I2S variantas)"""
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
            print(f"[ERROR] Audio klaida: {e}")
            return False

    async def uart_task(self):
        """UART ryšys fone"""
        try:
            reader, writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            print("[OK] UART ryšys aktyvus.")
            while True:
                writer.write(b'\x00')
                await writer.drain()
                await asyncio.sleep(5)
        except: print("[ERROR] UART nepavyko prisijungti.")

    async def main_loop(self):
        # Paleidžiame animaciją ir UART kaip atskiras užduotis
        asyncio.create_task(self.animation_loop())
        asyncio.create_task(self.uart_task())
        
        while True:
            # Kas 30 sekundžių padarome kontrolinį įrašą
            await asyncio.sleep(30)
            print("[*] Mikrofonas: pradedamas 2s testinis įrašas...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._record_audio_sync)

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nSustabdyta.")
