import asyncio
import os
import logging
from google import genai
from gtts import gTTS
import pygame

# Указываем драйвер звука для корректной работы на CM4 (PWM Audio)
os.environ['SDL_AUDIODRIVER'] = 'alsa'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        
        # Инициализация микшера pygame
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            self.logger.info("Звуковая система инициализирована (GPIO 12/13).")
        except Exception as e:
            self.logger.error(f"Ошибка звука: {e}")

        try:
            # Загрузка ключа
            key_path = os.path.join(BASE_DIR, "secrets.txt")
            with open(key_path, "r") as f:
                api_key = f.read().strip()
            
            # ПРИНУДИТЕЛЬНО используем версию v1, чтобы избежать ошибки 404
            self.client = genai.Client(
                api_key=api_key,
                http_options={'api_version': 'v1'}
            )
            self.logger.info("Sani: Интеллект подключен через v1 API.")
        except Exception as e:
            self.logger.error(f"Ошибка API: {e}")
            self.client = None

    async def monitor_wake_word(self):
        """ Цикл активации Сани (каждые 40 секунд для теста) """
        while True:
            await asyncio.sleep(40) 
            yield True

    async def record_audio(self, duration=3):
        """ Заглушка для записи голоса """
        self.logger.info("Слушаю...")
        await asyncio.sleep(duration)
        return "voice_data"

    async def send_to_gemini(self, audio_data):
        """ Отправка запроса в Gemini 1.5 Flash без ошибок 404 """
        if not self.client: return "ОШИБКА КОНФИГУРАЦИИ"
        
        try:
            # Используем стабильную версию модели
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents="Ты — злой робот Сани. Отвечай на русском языке, очень коротко."
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Gemini API Error: {e}")
            return "ОШИБКА СЕРВЕРА. ПОПРОБУЙ ПОЗЖЕ."

    async def speak(self, text):
        """ Озвучка через динамик на TDA1308 """
        try:
            filename = os.path.join(BASE_DIR, "res.mp3")
            self.logger.info(f"Генерация речи: {text}")
            
            # Создаем аудиофайл
            tts = gTTS(text=text, lang='ru')
            tts.save(filename)
            
            # Загружаем и проигрываем
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            # Ждем окончания проигрывания, не блокируя анимацию глаз
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Ошибка воспроизведения Сани: {e}")
