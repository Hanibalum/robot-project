try:
    import st7789
except ImportError:
    # If running in environment without st7789, it should be mocked before import
    pass

from PIL import Image
import os
import asyncio

class EvilSonicDisplay:
    def __init__(self, assets_dir="/home/cm4/robot-project/src/assets/"):
        self.assets_dir = assets_dir
        self.current_state = "static"
        self.frames = {}
        self.frame_counter = 0
        
        # Initialize ST7789 with CORRECT PINS (from Final Instructions)
        # Port=0
        # CS=0 (GPIO 8 / Physical 24)
        # DC=24 (Physical 18)
        # RST=25 (Physical 22)
        
        self.disp = st7789.ST7789(
            port=0,
            cs=0,       # GPIO 8
            dc=24,      # GPIO 24
            rst=25,     # GPIO 25
            backlight=None, 
            spi_speed_hz=80 * 1000 * 1000
        )
        
        # Initialize display
        self.disp.begin()
        self.width = self.disp.width
        self.height = self.disp.height
        
        # Preload assets
        self.load_assets()

    def load_assets(self):
        """Loads PNG frames for ONLY the valid states."""
        # Valid Folders: static, speaking, angry, laughing, shook
        states = ["static", "speaking", "angry", "laughing", "shook"]
        
        for state in states:
            self.frames[state] = []
            path = os.path.join(self.assets_dir, state)
            if os.path.exists(path):
                # Load and sort by filename
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    try:
                        img = Image.open(os.path.join(path, f))
                        # Resize to 240x320 if needed
                        img = img.resize((240, 320))
                        self.frames[state].append(img)
                    except Exception as e:
                        print(f"Error loading {f}: {e}")
            else:
                print(f"Warning: Asset folder not found: {path}")
                # Create a placeholder image
                img = Image.new('RGB', (240, 320), color=(0, 0, 0))
                self.frames[state].append(img)
                
    def get_next_frame(self):
        """Returns the next frame based on current state and frame_counter."""
        frames = self.frames.get(self.current_state, [])
        if not frames:
            return Image.new('RGB', (240, 320), (0, 0, 0))
            
        total_frames = len(frames)
        idx = 0
        
        # Smart Looping Logic for "angry" and "shook"
        # 1. Play Full Sequence (0 -> End) ONCE
        # 2. Then Ping-Pong Loop the last 50%
        if self.current_state in ["angry", "shook"] and total_frames > 1:
            if self.frame_counter < total_frames:
                # INTRO PHASE: Play linearly
                idx = self.frame_counter
            else:
                # LOOP PHASE: Ping-Pong last 50%
                loop_start = total_frames // 2
                loop_len = total_frames - loop_start
                
                if loop_len > 1:
                    # Frames elapsed since entering loop phase
                    frames_in_loop = self.frame_counter - total_frames
                    cycle_len = (loop_len * 2) - 2
                    
                    # Position in the ping-pong cycle (0 to cycle_len-1)
                    pos = frames_in_loop % cycle_len
                    
                    if pos < loop_len:
                        # Forward part of ping-pong
                        offset = pos
                    else:
                        # Backward part of ping-pong
                        offset = cycle_len - pos
                        
                    idx = loop_start + offset
                else:
                    # Fallback if too few frames to loop
                    idx = total_frames - 1
        else:
            # Standard Loop (static, speaking, laughing)
            # Cycle 0 -> End -> 0
            idx = self.frame_counter % total_frames
            
        return frames[idx]

    async def animate(self):
        """Main loop to update display."""
        while True:
            # 20 FPS -> 0.05s
            start_time = asyncio.get_event_loop().time()
            
            img = self.get_next_frame()
            self.disp.display(img)
            
            self.frame_counter += 1
            
            elapsed = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0.001, 0.05 - elapsed)
            await asyncio.sleep(sleep_time)

    def set_state(self, new_state):
        # Validates state and resets counter if changed
        if new_state in self.frames and new_state != self.current_state:
            self.current_state = new_state
            self.frame_counter = 0
