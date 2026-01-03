import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

class XGORobot:
    def __init__(self):
        # 1. Ekrano konfigūracija (Waveshare Nano B: CS=7, DC=24, RST=25)
        try:
            self.serial_spi = spi(port=0, device=1, gpio_DC=24, gpio_RST=25)
            self.device = st7789(self.serial_spi, width=240, height=320, rotation=0)
            self.display_active = True
            print("[OK] Ekranas inicijuotas.")
        except Exception as e:
            print(f"[ERROR] Ekranas: {e}")
            self.display_active = False

        # 2. UART nustatymai
        self.uart_port = '/dev/serial0'
        self.uart_writer = None

        # 3. Audio (Naudojame Card 0, kurią ką tik radome)
        self.audio = pyaudio.PyAudio()
        self.mic_index = 0 # Pagal arecord -l tavo mic yra Card 0

    def update_screen(self, status_text, color="green"):
        if not self.display_active: return
        img = Image.new("RGB", (240, 320), "black")
        draw = ImageDraw.Draw(img)
        draw.text((10, 150), f"STATUS: {status_text}", fill="white")
        draw.ellipse((100, 30, 140, 70), fill=color)
        self.device.display(img)

    async def init_uart(self):
        try:
            _, self.uart_writer = await serial_asyncio.open_serial_connection(url=self.uart_port, baudrate=115200)
            self.uart_writer.write(b'\x00') # Testinė komanda ESP32
            await self.uart_writer.drain()
            print(f"[OK] UART paruoštas ({self.uart_port}).")
        except Exception as e:
            print(f"[ERROR] UART klaida: {e}")

    def _record_audio_sync(self):
        CHUNK, FORMAT, CHANNELS, RATE = 1024, pyaudio.paInt16, 1, 44100
        try:
            stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                     input=True, input_device_index=self.mic_index,
                                     frames_per_buffer=CHUNK)
            frames = []
            for _ in range(0, int(RATE / CHUNK * 3)): # 3 sekundės
                frames.append(stream.read(CHUNK, exception_on_overflow=False))
            stream.stop_stream()
            stream.close()
            with wave.open("src/test.wav", 'wb') as wf:
                wf.setnchannels(CHANNELS); wf.setsampwidth(self.audio.get_sample_size(FORMAT)); wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            return True
        except Exception as e:
            print(f"[ERROR] Irasymas: {e}")
            return False

    async def main_loop(self):
        await self.init_uart()
        self.update_screen("READY", "green")
        
        while True:
            await asyncio.sleep(10)
            print("[*] Pradedamas 3s balso irasymas...")
            self.update_screen("RECORDING", "red")
            
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(None, self._record_audio_sync)
            
            if success:
                print("[OK] Garsas irasytas i src/test.wav")
                self.update_screen("SAVED", "blue")
                await asyncio.sleep(1)
            
            self.update_screen("READY", "green")

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nPrograma sustabdyta.")
