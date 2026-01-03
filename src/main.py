import asyncio
import wave
import pyaudio
import serial_asyncio
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

# Išjungiame įkyrius GPIO įspėjimus
GPIO.setwarnings(False)

class XGORobot:
    def __init__(self):
        # 1. Ekrano konfigūracija
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

        # 3. Audio (Nustatyta 16000Hz, kas tinka I2S mikrofonams)
        self.audio = pyaudio.PyAudio()
        self.mic_index = 0 

    def show_emotion(self, status_text, image_name="neutral.png"):
        """Užkrauna paveikslėlį iš assets arba nupiešia tekstą, jei failo nėra"""
        if not self.display_active: return
        
        try:
            # Bandome užkrauti EMO Pet vaizdą
            img = Image.open(f"src/assets/{image_name}").convert("RGB")
            img = img.resize((240, 320))
        except:
            # Jei paveikslėlio nėra, piešiame atsarginį vaizdą
            img = Image.new("RGB", (240, 320), "black")
            draw = ImageDraw.Draw(img)
            draw.text((10, 150), f"MISSING: {image_name}", fill="red")
            draw.text((10, 170), status_text, fill="white")
        
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
        # ICS-43434 reikalauja specifinio dažnio (16000 arba 48000)
        CHUNK, FORMAT, CHANNELS, RATE = 1024, pyaudio.paInt16, 1, 16000
        try:
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
            print(f"[ERROR] Mikrofonas: {e}")
            return False

    async def main_loop(self):
        await self.init_uart()
        self.show_emotion("SYSTEM READY", "neutral.png")
        
        while True:
            await asyncio.sleep(10)
            print("[*] Įrašinėju...")
            self.show_emotion("LISTENING", "recording.png")
            
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(None, self._record_audio_sync)
            
            if success:
                self.show_emotion("DONE", "neutral.png")
            else:
                self.show_emotion("MIC ERROR", "error.png")
            
            await asyncio.sleep(2)

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nSustabdyta.")
