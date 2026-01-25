import asyncio
import os
import logging
import google.generativeai as genai
from gtts import gTTS
import pygame

# Базовая директория проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        # Инициализация звукового движка pygame
        pygame.mixer.init()
        
        try:
            # Загружаем API ключ из локального файла
            key_path = os.path.join(BASE_DIR, "secrets.txt")
            with open(key_path, "r") as f:
                api_key = f.read().strip()
            
            genai.configure(api_key=api_key)
            # Используем стабильную модель gemini-1.5-flash
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("Gemini готов к работе через системный SDK.")
        except Exception as e:
            self.logger.error(f"Ошибка инициализации Gemini: {e}")
            self.model = None

    async def monitor_wake_word(self):
        """ Цикл ожидания команды. Для защиты от лимита API 429 - задержка 40 сек. """
        while True:
            await asyncio.sleep(40) 
            yield True

    async def record_audio(self, duration=3):
        """ Имитация записи голоса (здесь будет Vosk) """
        self.logger.info("Слушаю голос...")
        await asyncio.sleep(duration)
        return "simulate_data"

    async def send_to_gemini(self, audio_data):
        """ Отправка запроса в Google AI """
        if not self.model: return "API КЛЮЧ НЕ НАЙДЕН"
        
        # Инструкция для ИИ: отвечать коротко и быть злым Сани
        prompt = "Ты — злой робот Сани. Отвечай на русском языке, очень коротко (до 7 слов) и угрожающе."
        
        try:
            # Используем v1beta через старую библиотеку (это решит проблему 404)
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            self.logger.error(f"Ошибка запроса: {e}")
            return "ЛИМИТ ЗАПРОСОВ. ПОДОЖДИТЕ."

    async def speak(self, text):
        """ Превращение текста в голос через динамик TDA1308 """
        try:
            self.logger.info(f"Сани говорит: {text}")
            tts = gTTS(text=text, lang='ru')
            filename = os.path.join(BASE_DIR, "response.mp3")
            tts.save(filename)
            
            # Воспроизведение через GPIO 12/13 (PWM Audio)
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Ошибка динамика: {e}")
