#!/usr/bin/env python3
"""
Fixed version with:
1. Special handling for Cycle 0 (first run)
2. Fixed confirmation timer
3. Improved voice detection responsiveness
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

class WarpVoiceFix:
    def __init__(self):
        # Audio thresholds
        self.silence_threshold = 0.012  # Increased sensitivity
        self.silence_duration = 3.0
        self.confirmation_silence = 10.0
        self.min_audio_duration = 0.2
        
        # State tracking
        self.is_recording = False
        self.is_confirming = False
        self.manual_confirm = False
        self.cycle_count = 0
        self.last_sound_time = time.time()
        self.running = True
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.chunk = 512  # Reduced chunk size for faster processing
        self.format = pyaudio.paFloat32
        self.channels = 1
        self.rate = 44100
        
        # GUI setup
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.2
        
        # Load button position
        self.load_button_position()
        
        # Setup keyboard listener
        self.key_listener = keyboard.Listener(on_press=self.on_key_press)
        self.key_listener.start()
    
    def on_key_press(self, key):
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
        config_file = Path.home() / '.warp_controller_config.json'
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.button_pos = pyautogui.Point(
                config['record_button']['x'], 
                config['record_button']['y']
            )
            print("✅ Button position loaded")
        except Exception as e:
            print(f"❌ Could not load button position: {e}")
            exit(1)
    
    def focus_warp(self):
        try:
            result = subprocess.run(['xwininfo', '-tree', '-root'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'dev.warp.Warp' in line:
                        window_id = line.strip().split()[0]
                        subprocess.run(['wmctrl', '-i', '-a', window_id],
                                    capture_output=True)
                        time.sleep(0.5)  # Reduced delay
                        return True
            return False
        except Exception:
            return False
    
    def click_button(self, action):
        try:
            print(f"\n🎯 {action}")
            if not self.focus_warp():
                print("⚠️  Failed to focus Warp")
                return False
            
            pyautogui.click(self.button_pos)
            time.sleep(0.2)  # Short delay after click
            
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
        try:
            audio_data = np.frombuffer(data, dtype=np.float32)
            rms = np.sqrt(np.mean(audio_data**2))
            return rms
        except Exception:
            return 0.0
    
    def handle_confirmation(self, stream):
        print("\n⌛ Starting confirmation timer...")
        confirmation_start = time.time()
        samples_above_threshold = 0  # Count samples above threshold
        
        while self.running:
            data = stream.read(self.chunk, exception_on_overflow=False)
            level = self.get_audio_level(data)
            current_time = time.time()
            
            # Voice detection with threshold counting
            if level > self.silence_threshold:
                samples_above_threshold += 1
                if samples_above_threshold >= 2:  # Reduced required samples for faster response
                    print("\n🗣️  Voice detected - canceling confirmation")
                    if self.click_button("START RECORDING"):
                        print("✅ Recording resumed")
                    return False
            else:
                samples_above_threshold = 0  # Reset counter
            
            # Check for confirmation conditions
            elapsed = current_time - confirmation_start
            if self.manual_confirm:
                print("\n✅ Manual confirmation accepted")
                return True
            elif elapsed >= self.confirmation_silence:
                print(f"\n✅ Auto-confirmed after {self.confirmation_silence}s silence")
                return True
            
            # Show progress
            progress = elapsed / self.confirmation_silence * 20
            bar = "█" * int(progress) + "░" * (20 - int(progress))
            status = "[SPACE] to confirm now" if not self.manual_confirm else "Confirmed!"
            print(f"Confirming: [{bar}] {elapsed:.1f}s | {status}", end='\r')
            
            time.sleep(0.05)
    
    def run(self):
        print("=== Warp Voice Control ===")
        
        # Focus Warp window
        if not self.focus_warp():
            print("⚠️  Please ensure Warp is visible")
            return
        
        # Initialize audio
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
        except Exception as e:
            print(f"❌ Audio setup failed: {e}")
            return
        
        print("\n🎙️  Ready for voice input!")
        
        try:
            last_level_check = time.time()
            voice_active = False
            
            while self.running:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                audio_level = self.get_audio_level(data)
                current_time = time.time()
                
                # Voice detection
                if audio_level > self.silence_threshold:
                    self.last_sound_time = current_time
                    
                    if not voice_active:
                        voice_active = True
                        if not self.is_recording and not self.is_confirming:
                            self.click_button("START RECORDING")
                            print(f"🎤 Recording... (Cycle {self.cycle_count})")
                    
                    if self.is_recording:
                        if current_time - last_level_check >= 0.5:
                            print(f"Recording - Audio: {audio_level:.4f}", end='\r')
                            last_level_check = current_time
                
                # Silence detection
                else:
                    voice_active = False
                    if self.is_recording:
                        silence_time = current_time - self.last_sound_time
                        if current_time - last_level_check >= 0.2:
                            print(f"Recording - Silence: {silence_time:.1f}s", end='\r')
                            last_level_check = current_time
                        
                        if silence_time >= self.silence_duration:
                            print(f"\n⏸️  Stopping after {self.silence_duration}s silence")
                            if self.click_button("STOP RECORDING"):
                                time.sleep(0.2)  # Brief pause before confirmation
                                if self.handle_confirmation(self.stream):
                                    print("\n✅ Input confirmed!")
                                    self.click_button("SEND INPUT")
                                    print(f"\n🎙️  Ready for next input (Cycle {self.cycle_count})")
                                else:
                                    print("\n🔄 Confirmation canceled - continuing recording")
                
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            print("\n\n✅ Stopped by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        if self.key_listener:
            self.key_listener.stop()

if __name__ == "__main__":
    controller = WarpVoiceFix()
    controller.run()
