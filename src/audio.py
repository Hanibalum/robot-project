import asyncio
import os
import logging
import google.generativeai as genai
from gtts import gTTS
import pygame

# Путь к основной директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        # Инициализация звука для вывода на GPIO 12/13
        pygame.mixer.init()
        
        try:
            # Загружаем ключ из secrets.txt
            key_path = os.path.join(BASE_DIR, "secrets.txt")
            with open(key_path, "r") as f:
                api_key = f.read().strip()
            
            genai.configure(api_key=api_key)
            # Используем gemini-pro, так как он самый стабильный для этой библиотеки
            self.model = genai.GenerativeModel('gemini-pro')
            self.logger.info("Gemini готов. Используется модель gemini-pro для стабильности.")
        except Exception as e:
            self.logger.error(f"Ошибка ключа: {e}")
            self.model = None

    async def monitor_wake_word(self):
        """ Цикл ожидания команды 'САНИ' (пока эмуляция для теста) """
        while True:
            await asyncio.sleep(40) 
            yield True

    async def record_audio(self, duration=3):
        """ Имитация записи голоса """
        self.logger.info("Слушаю пользователя...")
        await asyncio.sleep(duration)
        return "fake_audio_data"

    async def send_to_gemini(self, audio_data):
        """ Отправка запроса в Google AI """
        if not self.model: return "ОШИБКА КОНФИГУРАЦИИ"
        
        # Четкая инструкция для Сани
        prompt = "Ты — злой робот по имени Сани. Отвечай на русском языке, очень коротко и угрожающе."
        
        try:
            # Прямой вызов модели без лишних параметров
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            self.logger.error(f"Ошибка DI: {e}")
            return "СИСТЕМА ПЕРЕГРУЖЕНА. ЖДИТЕ."

    async def speak(self, text):
        """ Озвучка текста через TDA1308 (PWM Audio на GPIO 12/13) """
        try:
            self.logger.info(f"Голос Сани: {text}")
            tts = gTTS(text=text, lang='ru')
            filename = os.path.join(BASE_DIR, "res.mp3")
            tts.save(filename)
            
            # Загрузка и воспроизведение
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Ошибка воспроизведения: {e}")
