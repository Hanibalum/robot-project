import sys
import os
import asyncio
import logging

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

# Try to import mocks
try:
    import mocks
except ImportError:
    pass

from display import EvilSonicDisplay

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestEmotions")

async def test_cycle():
    logger.info("Starting Emotion Cycle Test...")
    logger.info("Verifying Pin Configuration in Display...")
    
    # Initialize display
    # This will use the UPDATED pinout: CS=0, DC=24, RST=25
    display = EvilSonicDisplay()
    
    # Start animation loop in background
    anim_task = asyncio.create_task(display.animate())
    
    # Cycle through ONLY the 5 valid assets
    states = ["static", "speaking", "angry", "laughing", "shook"]
    
    try:
        while True:
            for state in states:
                logger.info(f"Testing State: {state}")
                display.set_state(state)
                
                # Show for 5 seconds to verify looping behavior
                # 'angry'/'shook' -> Check for Ping-Pong loop
                # 'static' -> Check for standard loop
                await asyncio.sleep(5)
            
            logger.info("Cycle complete. Restarting...")
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        anim_task.cancel()
        logger.info("Test stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(test_cycle())
    except KeyboardInterrupt:
        pass
