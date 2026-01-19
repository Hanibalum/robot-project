import asyncio
import logging
import random

# Saugus importas: jei bibliotekos nėra, programa nenulūš
try:
    from xgolib import XGO
    XGO_AVAILABLE = True
except ImportError:
    XGO_AVAILABLE = False

class XgoController:
    def __init__(self):
        self.logger = logging.getLogger("XgoController")
        self.port = '/dev/serial0'
        self.robot = None

        if XGO_AVAILABLE:
            try:
                # Inicijuojame ryšį su ESP32 važiuokle
                self.robot = XGO(port=self.port)
                self.logger.info(f"Važiuoklė sėkmingai prijungta per {self.port}")
            except Exception as e:
                self.logger.error(f"Nepavyko prisijungti prie važiuoklės: {e}")
        else:
            self.logger.warning("xgolib biblioteka nerasta. Robotas veiks simuliacijos režimu.")

    async def heartbeat(self):
        """Siunčia kontrolinį signalą kas 5 sekundes"""
        self.logger.info("Heartbeat užduotis paleista.")
        while True:
            try:
                if self.robot:
                    # Siunčiame bazinę komandą (pvz., baterijos būsenos nuskaitymą), 
                    # kad palaikytume UART ryšį aktyvų
                    self.robot.read_battery() 
            except Exception as e:
                self.logger.error(f"Heartbeat klaida: {e}")
            
            await asyncio.sleep(5)

    def perform_action(self, emotion):
        """Fizinis judesys pagal emociją"""
        if not self.robot:
            self.logger.info(f"[SIMULIACIJA] Judesys emocijai: {emotion}")
            return

        self.logger.info(f"Vykdomas judesys: {emotion}")
        try:
            if emotion == "angry":
                self.robot.pitch(15) # Pasilenkia į priekį
            elif emotion == "laughing":
                self.robot.action(4) # Šokinėjimas / šokis
            elif emotion == "shook":
                self.robot.roll(10)  # Susvyravimas į šoną
            elif emotion == "speaking":
                self.robot.pitch(5)  # Lengvas judesys kalbant
            else:
                self.robot.reset()   # Grįžta į pradinę padėtį (IDLE)
        except Exception as e:
            self.logger.error(f"Judesio klaida: {e}")
