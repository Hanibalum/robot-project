import time
import os
import spidev
import RPi.GPIO as GPIO
import numpy as np
from PIL import Image, ImageDraw
import threading
import asyncio

# Класс для управления экраном Сани
class EvilSonicDisplay:
    def __init__(self, assets_dir="/home/cm4/robot-project/src/assets/"):
        self.assets_dir = assets_dir
        self.current_state = "static"
        self.frame_buffer = []
        self.lock = threading.Lock()
        self.frame_counter = 0
        self.overlay_text = "" 
        
        # Настройка пинов (GPIO)
        self.DC, self.RST = 24, 25
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.DC, self.RST], GPIO.OUT)

        # Настройка SPI шины
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 40000000 
        self.spi.mode = 0b11 
        
        self._init_st7789()
        self.load_assets("static") 
        
        # Запуск отдельного потока для отрисовки (чтобы не лагало)
        self.running = True
        self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self.render_thread.start()

    def _init_st7789(self):
        # Аппаратный сброс дисплея
        GPIO.output(self.RST, GPIO.LOW); time.sleep(0.1); GPIO.output(self.RST, GPIO.HIGH); time.sleep(0.1)
        # Команды инициализации для TZT 2.0"
        for cmd, data in [(0x01, None), (0x11, None), (0x3A, [0x05]), (0x36, [0x70]), (0x21, None), (0x29, None)]:
            GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([cmd])
            if data: GPIO.output(self.DC, GPIO.HIGH); self.spi.writebytes(data)
            time.sleep(0.1)

    def load_assets(self, state):
        # Загрузка кадров анимации из папки
        path = os.path.join(self.assets_dir, state)
        new_frames = []
        if os.path.exists(path):
            files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
            for f in files:
                img = Image.open(os.path.join(path, f)).convert("RGB").resize((320, 240))
                new_frames.append(img)
        
        with self.lock:
            self.frame_buffer = new_frames
            self.current_state = state
            self.frame_counter = 0

    def _apply_overlay(self, img):
        # Рисуем "кровавую" панель Сани с текстом от ИИ
        if not self.overlay_text: return img
        draw_img = img.copy()
        draw = ImageDraw.Draw(draw_img)
        draw.rectangle((0, 180, 320, 240), fill=(0, 0, 0)) # Черный фон
        draw.line((0, 180, 320, 180), fill=(200, 0, 0), width=3) # Красная линия
        draw.text((10, 190), self.overlay_text[:45], fill=(255, 255, 255)) # Текст
        return draw_img

    def _render_loop(self):
        # Основной цикл отрисовки кадров
        while self.running:
            with self.lock:
                if not self.frame_buffer: 
                    time.sleep(0.1); continue
                img = self.frame_buffer[self.frame_counter % len(self.frame_buffer)]
            
            final_img = self._apply_overlay(img)
            img_np = np.array(final_img).astype(np.uint16)
            # Конвертация в формат RGB565 для дисплея
            color = ((img_np[:,:,0] & 0xF8) << 8) | ((img_np[:,:,1] & 0xFC) << 3) | (img_np[:,:,2] >> 3)
            pixel_bytes = np.stack(((color >> 8).astype(np.uint8), (color & 0xFF).astype(np.uint8)), axis=-1).tobytes()

            # Отправка данных по SPI
            GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([0x2A]); GPIO.output(self.DC, GPIO.HIGH); self.spi.writebytes([0, 0, 1, 0x3F])
            GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([0x2B]); GPIO.output(self.DC, GPIO.HIGH); self.spi.writebytes([0, 0, 0, 0xEF])
            GPIO.output(self.DC, GPIO.LOW); self.spi.writebytes([0x2C]); GPIO.output(self.DC, GPIO.HIGH)
            for i in range(0, len(pixel_bytes), 4096):
                self.spi.writebytes(list(pixel_bytes[i:i+4096]))
            
            self.frame_counter += 1
            time.sleep(0.04)

    def set_overlay(self, text):
        self.overlay_text = text.upper()

    def set_state(self, state):
        # Поток для смены эмоции
        threading.Thread(target=self.load_assets, args=(state,), daemon=True).start()

    async def animate(self):
        while self.running: await asyncio.sleep(1)
