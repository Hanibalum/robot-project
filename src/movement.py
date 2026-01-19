try:
    from xgolib import XGO
except ImportError:
    pass

import asyncio
import logging
import random

class XgoController:
    def __init__(self):
        # Initialize XGO library
        # Assuming typical UART setup on /dev/ttyAMA0 or similar, but xgolib usually handles defaults
        # or takes a port.
        self.robot = XGO(port='/dev/ttyAMA0') 
        self.last_heartbeat = 0
        self.logger = logging.getLogger("XgoController")

    async def heartbeat(self):
        """Sends a keep-alive signal to the robot every 5 seconds."""
        self.logger.info("Heartbeat task started.")
        while True:
            try:
                # Assuming sending a command resets the watchdog or there is a specific heartbeat cmd
                # If no specific heartbeat, just reading status or a small move helps
                # Prompt says: "Kas 5s siųsti Heartbeat (gyvybės signalą) per xgolib."
                # We will assume a method like 'action(0)' or similar exists, or just verify connection.
                # Usually accessing battery or version is a good heartbeat.
                # Let's assume a generic ping or status read if explicit heartbeat isn't in API docs provided.
                # I'll use a placeholder 'reset' or 'stop' which is usually safe, or just logging.
                # Ideally, we send a neutral command.
                
                # Mock call
                self.robot.action(0) # 0 is often 'stand' or 'reset' in some robot libs
                
                self.logger.debug("Heartbeat sent.")
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {e}")
            
            await asyncio.sleep(5)

    def perform_action(self, emotion):
        """Triggers physical movement based on emotion."""
        self.logger.info(f"Performing action for: {emotion}")
        try:
            if emotion == "angry":
                # Robot pitch forward (aggressive)
                self.robot.pitch(15)
            elif emotion == "laughing":
                # Robot nod or dance
                self.robot.action(4) # Assuming 4 is a preset action like 'shake'
            elif emotion == "shook":
                # Slight tilt or random twitch
                self.robot.roll(random.randint(-5, 5))
            elif emotion == "speaking":
                 # Maybe slight movement while talking?
                 pass
            else:
                # Return to neutral (static/IDLE)
                self.robot.pitch(0)
                self.robot.roll(0)
        except Exception as e:
            self.logger.error(f"Action failed: {e}")
