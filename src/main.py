import asyncio
import logging
from display import EvilSonicDisplay
from movement import XgoController
from audio import AudioBrain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")

async def main():
    logger.info("Starting Evil Sonic...")
    
    display = EvilSonicDisplay()
    controller = XgoController()
    brain = AudioBrain()
    
    # Paleidžiame užduotis
    asyncio.create_task(controller.heartbeat())
    asyncio.create_task(display.animate()) # Dabar šitas nesuluš
    
    try:
        async for _ in brain.monitor_wake_word():
            logger.info("Triggered!")
            display.set_state("speaking")
            
            audio_data = await brain.record_audio(duration=3)
            display.set_state("shook")
            
            response = await brain.send_to_gemini(audio_data)
            logger.info(f"AI: {response}")
            
            # Paprasta emocijų logika
            if "piktas" in response.lower(): display.set_state("angry")
            else: display.set_state("static")
            
            await asyncio.sleep(5)
            display.set_state("static")
            
    except Exception as e:
        logger.error(f"Klaida: {e}")

if __name__ == "__main__":
    asyncio.run(main())
