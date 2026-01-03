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
        # 1. Ekranas
        try:
            self.serial_spi = spi(port=0, device=1, gpio_DC=24, gpio_RST=25)
            self.device = st7789(self.serial_spi, width=240, height=320, rotation=0)
            self.display_active = True
        except Exception as e:
            print(f"[ERROR] Ekranas: {e}")
            self.display_active = False

        # 2. UART
        self.uart_port = '/dev/serial0'
        self.uart_writer = None

        # 3. Audio paieška
        self.audio = pyaudio.PyAudio()
        self.mic_index = self._find_mic_index()

    def _find_mic_index(self):
        """Suranda I2S įrenginio ID"""
        for i in range(self.audio.get_device_count()):
            dev = self.audio.get_device_info_by_index(i)
            if "mic" in dev['name'].lower() or "i2s" in dev['name'].lower():
                print(f"[OK] Rastas mikrofonas: {dev['name']} (Index: {i})")
                return i
        print("[WARNING] Mikrofonas nerastas!")
        return None

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
            self.uart_writer.write(b'\x00')
            await self.uart_writer.drain()
            print(f"[OK] UART paruoštas.")
        except:
            print(f"[ERROR] UART nepavyko.")

    def _record_audio_sync(self):
        if self.mic_index is None: return False
        try:
            CHUNK, FORMAT, CHANNELS, RATE = 1024, pyaudio.paInt16, 1, 44100
            stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                     input=True, input_device_index=self.mic_index,
                                     frames_per_buffer=CHUNK)
            frames = []
            for _ in range(0, int(RATE / CHUNK * 3)):
                frames.append(stream.read(CHUNK, exception_on_overflow=False))
            stream.stop_stream()
            stream.close()
            with wave.open("src/test.wav", 'wb') as wf:
                wf.setnchannels(CHANNELS); wf.setsampwidth(self.audio.get_sample_size(FORMAT)); wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            return True
        except Exception as e:
            print(f"Irasymo klaida: {e}")
            return False

    async def main_loop(self):
        await self.init_uart()
        self.update_screen("READY")
        
        while True:
            await asyncio.sleep(10)
            if self.mic_index is not None:
                self.update_screen("RECORDING", color="red")
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._record_audio_sync)
                self.update_screen("READY")
            else:
                self.update_screen("NO MIC", color="orange")
                await asyncio.sleep(5)

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
