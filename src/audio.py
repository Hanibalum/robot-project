import asyncio
import os
import logging
from google import genai
from gtts import gTTS
import pygame

# Путь к папке проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        # Инициализация звука для вывода на GPIO 12/13
        pygame.mixer.init()
        
        try:
            # Загружаем API ключ
            key_path = os.path.join(BASE_DIR, "secrets.txt")
            with open(key_path, "r") as f:
                api_key = f.read().strip()
            
            # Инициализируем НОВЫЙ клиент Google GenAI
            self.client = genai.Client(api_key=api_key)
            self.logger.info("Sani: Интеллект Gemini 1.5 Flash подключен через новый SDK.")
        except Exception as e:
            self.logger.error(f"Ошибка ключа: {e}")
            self.client = None

    async def monitor_wake_word(self):
        """ Цикл активации. Для тестов — раз в 40 секунд. """
        while True:
            await asyncio.sleep(40) 
            yield True

    async def record_audio(self, duration=3):
        """ Заглушка для записи голоса """
        self.logger.info("Слушаю...")
        await asyncio.sleep(duration)
        return "simulate_data"

    async def send_to_gemini(self, audio_data):
        """ Отправка запроса в Google AI через новый метод """
        if not self.client: return "ОШИБКА АПИ"
        
        try:
            # Новый формат вызова Gemini 1.5 Flash (без v1beta в URL)
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents="Ты — злой робот по имени Сани. Отвечай на русском языке, коротко (до 10 слов)."
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Ошибка Gemini: {e}")
            return "СИСТЕМА ЗАНЯТА. ПОДОЖДИТЕ."

    async def speak(self, text):
        """ Озвучка через динамик на TDA1308 """
        try:
            self.logger.info(f"Сани говорит: {text}")
            tts = gTTS(text=text, lang='ru')
            filename = os.path.join(BASE_DIR, "res.mp3")
            tts.save(filename)
            
            # Воспроизведение через pygame
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Ошибка звука: {e}")
