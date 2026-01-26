import asyncio
import os
import logging
import google.generativeai as genai
from gtts import gTTS
import pygame

# Указываем драйвер звука для CM4
os.environ['SDL_AUDIODRIVER'] = 'alsa'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        
        # Инициализация звука
        try:
            pygame.mixer.init()
            self.logger.info("Аудиосистема готова.")
        except Exception as e:
            self.logger.error(f"Ошибка звука: {e}")

        try:
            # Загрузка ключа из secrets.txt
            key_path = os.path.join(BASE_DIR, "secrets.txt")
            with open(key_path, "r") as f:
                api_key = f.read().strip()
            
            # Настройка стабильной библиотеки
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("Sani: Интеллект Gemini 1.5 Flash подключен (Stable SDK).")
        except Exception as e:
            self.logger.error(f"Ошибка API: {e}")
            self.model = None

    async def monitor_wake_word(self):
        """ Цикл активации Сани """
        while True:
            await asyncio.sleep(30) 
            yield True

    async def record_audio(self, duration=3):
        """ Заглушка записи """
        self.logger.info("Слушаю...")
        await asyncio.sleep(duration)
        return "data"

    async def send_to_gemini(self, audio_data):
        """ Отправка запроса через стабильный метод """
        if not self.model: return "ОШИБКА КОНФИГУРАЦИИ"
        
        try:
            # Прямой вызов модели (без лишних префиксов в URL)
            response = await asyncio.to_thread(
                self.model.generate_content,
                "Ты — злой робот Сани. Отвечай на русском языке, очень коротко и угрожающе."
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Ошибка Gemini: {e}")
            return "СЕТЕВАЯ ОШИБКА"

    async def speak(self, text):
        """ Озвучка текста через динамик """
        try:
            filename = os.path.join(BASE_DIR, "res.mp3")
            self.logger.info(f"Голос Сани: {text}")
            
            # Генерация файла
            tts = gTTS(text=text, lang='ru')
            tts.save(filename)
            
            # Воспроизведение
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Ошибка динамика: {e}")
