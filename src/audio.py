import asyncio
import os
import logging
import google.generativeai as genai
from gtts import gTTS
import pygame

# Настройка аудио-драйвера для CM4
os.environ['SDL_AUDIODRIVER'] = 'alsa'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class AudioBrain:
    def __init__(self):
        self.logger = logging.getLogger("AudioBrain")
        
        # Инициализация звука для вывода на GPIO 12/13
        try:
            pygame.mixer.init()
            self.logger.info("Аудиосистема готова (ALSA).")
        except Exception as e:
            self.logger.error(f"Ошибка звука: {e}")

        try:
            # Загрузка ключа из secrets.txt
            key_path = os.path.join(BASE_DIR, "secrets.txt")
            with open(key_path, "r") as f:
                api_key = f.read().strip()
            
            genai.configure(api_key=api_key)
            
            # АВТОМАТИЧЕСКИЙ ПОИСК ДОСТУПНОЙ МОДЕЛИ
            # Это исключит ошибку 404, так как мы возьмем только то, что работает
            self.model_name = 'gemini-1.5-flash' # По умолчанию
            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                if 'models/gemini-1.5-flash' in available_models:
                    self.model_name = 'gemini-1.5-flash'
                elif 'models/gemini-pro' in available_models:
                    self.model_name = 'gemini-pro'
                else:
                    self.model_name = available_models[0].split('/')[-1]
                self.logger.info(f"Используется модель: {self.model_name}")
            except:
                self.logger.warning("Не удалось составить список моделей, пробуем стандарт.")

            self.model = genai.GenerativeModel(self.model_name)
            self.logger.info("Sani: Интеллект подключен.")
        except Exception as e:
            self.logger.error(f"Ошибка API: {e}")
            self.model = None

    async def monitor_wake_word(self):
        """ Цикл активации. Сейчас — каждые 30 секунд для тестов. """
        while True:
            await asyncio.sleep(30) 
            yield True

    async def record_audio(self, duration=3):
        """ Здесь будет интеграция с Vosk/Микрофоном """
        self.logger.info("Слушаю...")
        await asyncio.sleep(duration)
        return "voice_data"

    async def send_to_gemini(self, audio_data):
        """ Отправка запроса без ошибок 404 """
        if not self.model: return "ОШИБКА КОНФИГУРАЦИИ"
        
        # Прямая инструкция для Сани
        prompt = "Ты — злой и циничный робот Сани. Отвечай на русском языке, очень коротко (до 10 слов)."
        
        try:
            # Используем выбранную модель
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            self.logger.error(f"Ошибка Gemini: {e}")
            return "СЕРВЕР НЕ ОТВЕЧАЕТ"

    async def speak(self, text):
        """ Озвучка текста через TDA1308 """
        try:
            filename = os.path.join(BASE_DIR, "res.mp3")
            self.logger.info(f"Голос Сани: {text}")
            
            # Генерация аудио
            tts = gTTS(text=text, lang='ru')
            tts.save(filename)
            
            # Загрузка и воспроизведение
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            # Ждем пока договорит, не блокируя анимацию глаз
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Ошибка воспроизведения: {e}")
