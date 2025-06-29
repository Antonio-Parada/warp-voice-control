#!/usr/bin/env python3
"""
Status Client for Warp Voice Control
Sends status updates to the overlay window via IPC
"""

import socket
import json
import threading
import time

class StatusClient:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.enabled = True
        
    def send_update(self, **kwargs):
        """Send status update to overlay"""
        if not self.enabled:
            return
            
        try:
            # Create socket and send data
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(0.1)  # Quick timeout
            client_socket.connect((self.host, self.port))
            
            # Prepare update data
            update_data = json.dumps(kwargs)
            client_socket.send(update_data.encode('utf-8'))
            client_socket.close()
            
        except Exception as e:
            # Silently fail if overlay isn't running
            # print(f"Status update failed: {e}")
            pass
    
    def update_recording(self, recording):
        """Update recording status"""
        self.send_update(recording=recording)
    
    def update_confirming(self, confirming):
        """Update confirmation status"""
        self.send_update(confirming=confirming)
    
    def update_audio_level(self, level):
        """Update audio level"""
        self.send_update(audio_level=level)
    
    def update_timer(self, timer_value):
        """Update timer display"""
        self.send_update(timer=timer_value)
    
    def update_cycle(self, cycle_count):
        """Update cycle counter"""
        self.send_update(cycle=cycle_count)
    
    def update_status(self, status_text):
        """Update status text"""
        self.send_update(status_text=status_text)
    
    def disable(self):
        """Disable status updates"""
        self.enabled = False
    
    def enable(self):
        """Enable status updates"""
        self.enabled = True
