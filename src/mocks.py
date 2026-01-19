from unittest.mock import MagicMock
import sys
import types

# Mock st7789
st7789_mock = types.ModuleType("st7789")
st7789_mock.ST7789 = MagicMock()
sys.modules["st7789"] = st7789_mock

# Mock xgolib
xgolib_mock = types.ModuleType("xgolib")
xgolib_mock.XGO = MagicMock()
sys.modules["xgolib"] = xgolib_mock

# Mock sounddevice
sd_mock = types.ModuleType("sounddevice")
sd_mock.InputStream = MagicMock()
sd_mock.query_devices = MagicMock(return_value=[{'name': 'snd_rpi_i2s_card', 'max_input_channels': 2}])
sys.modules["sounddevice"] = sd_mock

# Mock vosk
vosk_mock = types.ModuleType("vosk")
vosk_mock.Model = MagicMock()
vosk_mock.KaldiRecognizer = MagicMock()
sys.modules["vosk"] = vosk_mock

# Mock google.generativeai
genai_mock = types.ModuleType("google.generativeai")
genai_mock.configure = MagicMock()
genai_mock.GenerativeModel = MagicMock()
sys.modules["google"] = types.ModuleType("google")
sys.modules["google.generativeai"] = genai_mock

# Mock RPi.GPIO (needed by st7789 usually, though st7789 library might handle it)
gpio_mock = types.ModuleType("RPi.GPIO")
gpio_mock.setmode = MagicMock()
gpio_mock.setup = MagicMock()
gpio_mock.output = MagicMock()
gpio_mock.BCM = "BCM"
gpio_mock.OUT = "OUT"
gpio_mock.HIGH = "HIGH"
gpio_mock.LOW = "LOW"
sys.modules["RPi"] = types.ModuleType("RPi")
sys.modules["RPi.GPIO"] = gpio_mock
