import sys
import os
import asyncio
import logging

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Try to import mocks only if specifically requested (DEV MODE)
# This prevents mocks from disabling real hardware on the robot
if os.environ.get("EVIL_SONIC_ENV") == "dev":
    try:
        import mocks
        logging.getLogger("Main").warning("Running in DEV mode with MOCKS enabled.")
    except ImportError:
        pass

from display import EvilSonicDisplay
from movement import XgoController
from audio import AudioBrain

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Main")

async def main():
    logger.info("Initializing Evil Sonic...")
    
    # Initialize modules
    display = EvilSonicDisplay()
    controller = XgoController()
    brain = AudioBrain()
    
    # Start background tasks
    # 1. Heartbeat - CRITICAL PRIORITY
    heartbeat_task = asyncio.create_task(controller.heartbeat())
    
    # 2. Display Animation
    display_task = asyncio.create_task(display.animate())
    
    # 3. Main Logic Loop (Audio -> AI -> Action)
    try:
        # Start listening loop
        async for _ in brain.monitor_wake_word():
            logger.info("Wake word detected!")
            
            # State: SPEAKING (Used as "Active/Listening" indicator)
            # We default to 'speaking' or 'static' when active.
            display.set_state("speaking")
            
            # Record Audio
            audio_data = await brain.record_audio(duration=3)
            
            # State: SHOOK (Used for "Thinking/Processing")
            display.set_state("shook")
            controller.perform_action("THINKING") 
            
            try:
                # Send to Cloud
                response_text = await brain.send_to_gemini(audio_data)
                logger.info(f"Gemini response: {response_text}")
                
                # Analyze sentiment & Map to Valid Emotions
                lower_text = response_text.lower()
                
                # Default emotion
                emotion = "speaking"
                
                if "evil" in lower_text or "angry" in lower_text or "destroy" in lower_text:
                    emotion = "angry"
                elif "happy" in lower_text or "funny" in lower_text or "laugh" in lower_text:
                    emotion = "laughing"
                elif "confused" in lower_text or "what" in lower_text or "shook" in lower_text:
                    emotion = "shook"
                
                # 1. Reaction Phase (if not just speaking)
                if emotion != "speaking":
                    display.set_state(emotion)
                    controller.perform_action(emotion) # Sync movement
                    # Hold the reaction for a moment
                    await asyncio.sleep(2)
                
                # 2. TTS Phase (Speaking)
                display.set_state("speaking")
                # await tts_speak(response_text)
                await asyncio.sleep(3) # Simulate TTS duration
                
                # 3. Return to Idle (Static)
                display.set_state("static")
                controller.perform_action("IDLE")
                
            except Exception as e:
                logger.error(f"Error during AI processing: {e}")
                
                # ERROR STATE -> Map to "shook" (Confused/Error)
                display.set_state("shook")
                controller.perform_action("EVIL_GLITCH") # Movement can still twitch
                
                # Recover after some time
                await asyncio.sleep(3)
                display.set_state("static")
                controller.perform_action("IDLE")
                
    except asyncio.CancelledError:
        logger.info("Main loop cancelled.")
    finally:
        # Clean up
        heartbeat_task.cancel()
        display_task.cancel()
        logger.info("Evil Sonic shutting down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
