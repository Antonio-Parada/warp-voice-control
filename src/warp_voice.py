#!/usr/bin/env python3
"""
Quick-start version with fixed audio initialization
and improved window focus handling
"""

import time
import threading
import subprocess
import pyaudio
import numpy as np
import pyautogui
import json
from pathlib import Path
from pynput import keyboard

class WarpQuickController:
    def __init__(self):
        # Configure before initializing hardware
        self.configure_settings()
        
        # Initialize core components in order
        self.init_audio_device()
        self.load_button_position()
        self.setup_keyboard()
    
    def configure_settings(self):
        """Configure settings before hardware init"""
        # Audio thresholds
        self.silence_threshold = 0.015
        self.silence_duration = 3.0
        self.confirmation_silence = 10.0
        self.min_audio_duration = 0.2
        
        # Audio parameters
        self.chunk = 1024
        self.format = pyaudio.paFloat32
        self.channels = 1
        self.rate = 44100
        
        # State tracking
        self.is_recording = False
        self.is_confirming = False
        self.manual_confirm = False
        self.cycle_count = 0
        self.last_sound_time = time.time()
        
        # GUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.2  # Reduced for quicker response
        
        # Flags
        self.audio_ready = False
        self.running = True
    
    def init_audio_device(self):
        """Initialize audio device with error handling"""
        try:
            self.audio = pyaudio.PyAudio()
            # Test open a stream to ensure it works
            test_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
                start=False  # Don't start yet
            )
            test_stream.close()
            self.audio_ready = True
            print("✅ Audio device initialized")
        except Exception as e:
            print(f"❌ Audio setup error: {e}")
            self.audio_ready = False
    
    def setup_keyboard(self):
        """Setup keyboard listener"""
        self.key_listener = keyboard.Listener(on_press=self.on_key_press)
        self.key_listener.start()
    
    def on_key_press(self, key):
        """Handle keyboard events"""
        try:
            if key == keyboard.Key.space and self.is_confirming:
                print("\n⌨️  Manual confirmation received!")
                self.manual_confirm = True
            elif key == keyboard.Key.esc:
                print("\n❌ Emergency stop requested")
                self.running = False
                return False
        except AttributeError:
            pass
    
    def load_button_position(self):
        """Load button position from config"""
        config_file = Path.home() / '.warp_controller_config.json'
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.button_pos = pyautogui.Point(
                config['record_button']['x'], 
                config['record_button']['y']
            )
            print("✅ Button position loaded")
            return True
        except Exception as e:
            print(f"❌ Button config error: {e}")
            return False
    
    def ensure_warp_focus(self):
        """Ensure Warp window is focused"""
        try:
            result = subprocess.run(['xwininfo', '-tree', '-root'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'dev.warp.Warp' in line:
                        window_id = line.strip().split()[0]
                        subprocess.run(['wmctrl', '-i', '-a', window_id],
                                    capture_output=True)
                        return True
            return False
        except Exception:
            return False
    
    def click_button(self, action):
        """Click button with minimal delay"""
        try:
            if self.ensure_warp_focus():
                time.sleep(0.1)  # Minimal delay
                pyautogui.click(self.button_pos)
                
                if action == "START RECORDING":
                    self.is_recording = True
                    self.is_confirming = False
                    self.manual_confirm = False
                elif action == "STOP RECORDING":
                    self.is_recording = False
                    self.is_confirming = True
                    self.manual_confirm = False
                elif action == "SEND INPUT":
                    self.is_recording = False
                    self.is_confirming = False
                    self.manual_confirm = False
                    self.cycle_count += 1
                    pyautogui.press('return')
                return True
        except Exception as e:
            print(f"❌ Click error: {e}")
        return False
    
    def get_audio_level(self, data):
        """Get audio level"""
        try:
            audio_data = np.frombuffer(data, dtype=np.float32)
            rms = np.sqrt(np.mean(audio_data**2))
            return rms
        except Exception:
            return 0.0
    
    def handle_confirmation(self, stream):
        """Handle confirmation with voice cancel"""
        print("\n=== Confirming Input ===")
        print("Options:")
        print("• SPACE to confirm now")
        print("• Wait 10s for auto-confirm")
        print("• Speak to continue")
        
        start_time = time.time()
        while self.running:
            data = stream.read(self.chunk, exception_on_overflow=False)
            level = self.get_audio_level(data)
            current_time = time.time()
            
            # Check for voice input
            if level > self.silence_threshold:
                print("\n🔄 Voice detected - continuing...")
                if self.click_button("START RECORDING"):
                    print("✅ Recording resumed")
                return False
            
            # Update progress bar
            elapsed = current_time - start_time
            progress = min(elapsed / self.confirmation_silence * 20, 20)
            bar = "█" * int(progress) + "░" * (20 - int(progress))
            status = "[SPACE] Confirm" if not self.manual_confirm else "✓ Confirmed"
            print(f"Auto-confirm: [{bar}] {elapsed:.1f}s | {status}", end='\r')
            
            # Check confirmations
            if self.manual_confirm or elapsed >= self.confirmation_silence:
                return True
            
            time.sleep(0.05)
        
        return False
    
    def run(self):
        """Main run loop with quick start"""
        print("=== Quick-Start Warp Controller ===")
        
        # Verify components
        if not self.audio_ready:
            print("❌ Audio device not ready")
            return
        
        if not self.ensure_warp_focus():
            print("⚠️ Please ensure Warp is open and visible")
            time.sleep(1)
        
        # Open audio stream
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        print("\n🎙️  Ready! Start speaking...")
        
        try:
            while self.running:
                if not stream.is_active():
                    stream.start_stream()
                
                data = stream.read(self.chunk, exception_on_overflow=False)
                level = self.get_audio_level(data)
                current_time = time.time()
                
                if level > self.silence_threshold:
                    self.last_sound_time = current_time
                    
                    if not self.is_recording and not self.is_confirming:
                        if self.click_button("START RECORDING"):
                            print(f"\n🎤 Recording... (Cycle {self.cycle_count})")
                    
                    if self.is_recording:
                        print(f"Recording - Audio: {level:.4f}", end='\r')
                
                elif self.is_recording:
                    silence_time = current_time - self.last_sound_time
                    print(f"Recording - Silence: {silence_time:.1f}s", end='\r')
                    
                    if silence_time >= self.silence_duration:
                        print(f"\n⏸️  Paused after {self.silence_duration}s silence")
                        if self.click_button("STOP RECORDING"):
                            if self.handle_confirmation(stream):
                                print("\n✅ Confirmed! Sending...")
                                self.click_button("SEND INPUT")
                                print(f"\n🎙️  Ready for next input (Cycle {self.cycle_count})")
                
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\n\n✅ Stopped by user")
        finally:
            stream.stop_stream()
            stream.close()
            self.audio.terminate()
            self.key_listener.stop()

if __name__ == "__main__":
    controller = WarpQuickController()
    controller.run()
