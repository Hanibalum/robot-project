import asyncio
import wave
import pyaudio
import serial_asyncio
from PIL import Image, ImageDraw
from luma.core.interface.serial import spi
from luma.lcd.device import st7789

class XGORobot:
    def __init__(self):
        # 1. Ekrano konfigūracija (GMT020-02 / ST7789)
        # Waveshare Nano B: CS=7 (device 1), DC=24, RST=25
        try:
            self.serial_spi = spi(port=0, device=1, gpio_DC=24, gpio_RST=25)
            self.device = st7789(self.serial_spi, width=240, height=320, rotation=0)
            self.display_active = True
            print("[OK] Ekranas paruoštas.")
        except Exception as e:
            print(f"[ERROR] Ekranas nerastas: {e}")
            self.display_active = False

        # 2. Garso konfigūracija (I2S ICS-43434)
        self.audio = pyaudio.PyAudio()
        
        # 3. UART (Ryšys su važiuokle)
        self.uart_reader = None
        self.uart_writer = None

    def update_screen(self, status_text, color="green"):
        """Nupiešia statusą be ekrano mirksėjimo (naudojant bufferį)"""
        if not self.display_active: return
        
        # Sukuriame naują kadrą
        img = Image.new("RGB", (240, 320), "black")
        draw = ImageDraw.Draw(img)
        
        # Pagrindinis statusas
        draw.text((10, 150), f"STATUS: {status_text}", fill="white")
        
        # Vizualus indikatorius (apskritimas viršuje)
        draw.ellipse((100, 30, 140, 70), fill=color)
        
        # Siunčiame kadrą į ekraną
        self.device.display(img)

    async def init_uart(self):
        """Inicijuoja UART ryšį ir siunčia starto signalą 0x00"""
        try:
            self.uart_reader, self.uart_writer = await serial_asyncio.open_serial_connection(
                url='/dev/ttyAMA0', baudrate=115200)
            self.uart_writer.write(b'\x00')
            await self.uart_writer.drain()
            print("[OK] UART ryšys aktyvus.")
        except Exception as e:
            print(f"[ERROR] UART klaida: {e}")

    async def uart_receiver_task(self):
        """Klauso duomenų iš ESP32 (važiuoklės)"""
        if not self.uart_reader: return
        while True:
            try:
                data = await self.uart_reader.read(100)
                if data:
                    print(f"[UART DATA]: {data.hex()}")
            except:
                pass
            await asyncio.sleep(0.1)

    def _record_audio_sync(self):
        """Sinchroninis 3s garso įrašymas (vykdomas atskiroje gijoje)"""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        RECORD_SECONDS = 3
        WAVE_OUTPUT_FILENAME = "src/test.wav"

        try:
            stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                                     input=True, frames_per_buffer=CHUNK)
            frames = []
            for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()

            with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
            return True
        except Exception as e:
            print(f"[ERROR] Mikrofonas: {e}")
            return False

    async def main_loop(self):
        """Pagrindinis asinhroninis ciklas"""
        # 1. Inicijavimas
        await self.init_uart()
        self.update_screen("READY", color="green")

        # 2. Užduočių paleidimas lygiagrečiai
        tasks = [
            asyncio.create_task(self.uart_receiver_task()),
        ]

        # 3. Darbo ciklas
        while True:
            # Kas 10 sekundžių darome balso įrašą (testui)
            await asyncio.sleep(10)
            self.update_screen("RECORDING...", color="red")
            
            # Naudojame run_in_executor, kad ekranas neužstrigtų įrašymo metu
            loop = asyncio.get_running_loop()
            success = await loop.run_in_executor(None, self._record_audio_sync)
            
            if success:
                self.update_screen("SAVED", color="blue")
                await asyncio.sleep(2)
            
            self.update_screen("READY", color="green")

if __name__ == "__main__":
    robot = XGORobot()
    try:
        asyncio.run(robot.main_loop())
    except KeyboardInterrupt:
        print("\nPrograma sustabdyta.")
