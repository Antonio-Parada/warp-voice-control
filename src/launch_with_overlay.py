#!/usr/bin/env python3
"""
Launch script for Warp Voice Control with Status Overlay
Starts both the voice control and the status overlay window
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    
    print("🚀 Starting Warp Voice Control with Status Overlay")
    
    # Start the status overlay first
    print("   Starting status overlay...")
    try:
        overlay_process = subprocess.Popen([
            sys.executable, 
            str(script_dir / "status_overlay.py")
        ])
        time.sleep(2)  # Give overlay time to start
        print("   ✅ Status overlay started")
    except Exception as e:
        print(f"   ⚠️ Failed to start overlay: {e}")
        overlay_process = None
    
    # Start the voice control
    print("   Starting voice control...")
    try:
        voice_process = subprocess.Popen([
            sys.executable,
            str(script_dir / "warp_voice.py")
        ])
        print("   ✅ Voice control started")
        
        # Wait for voice control to finish
        voice_process.wait()
        
    except KeyboardInterrupt:
        print("\n   🛑 Stopping processes...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        # Clean up processes
        if overlay_process:
            overlay_process.terminate()
            print("   ✅ Overlay stopped")

if __name__ == "__main__":
    main()
