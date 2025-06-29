#!/usr/bin/env python3
"""
Status Overlay for Warp Voice Control
Displays real-time status information over the Warp terminal window
"""

import tkinter as tk
from tkinter import ttk
import threading
import socket
import json
import time
import subprocess
from pathlib import Path

class WarpStatusOverlay:
    def __init__(self):
        self.window = tk.Tk()
        self.setup_window()
        self.setup_ui()
        self.setup_ipc()
        
        # State tracking
        self.current_state = {
            'recording': False,
            'confirming': False,
            'audio_level': 0.0,
            'timer': 0.0,
            'cycle': 0,
            'status_text': 'Ready'
        }
        
        # Start IPC listener
        self.ipc_thread = threading.Thread(target=self.listen_for_updates, daemon=True)
        self.ipc_thread.start()
        
    def setup_window(self):
        """Configure the overlay window"""
        self.window.title("Warp Voice Status")
        self.window.geometry("300x200+50+50")  # width x height + x_offset + y_offset
        
        # Make window stay on top and semi-transparent
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.85)
        
        # Remove window decorations for cleaner look
        self.window.overrideredirect(True)
        
        # Set background color
        self.window.configure(bg='#1a1a1a')
        
        # Make window draggable
        self.window.bind('<Button-1>', self.start_move)
        self.window.bind('<B1-Motion>', self.do_move)
        
    def setup_ui(self):
        """Create the UI elements"""
        # Main frame
        main_frame = tk.Frame(self.window, bg='#1a1a1a', padx=10, pady=10)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="🎙️ Warp Voice Control", 
                              fg='#00ff88', bg='#1a1a1a', 
                              font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Status indicator
        self.status_label = tk.Label(main_frame, text="Ready", 
                                   fg='#ffffff', bg='#1a1a1a',
                                   font=('Arial', 10))
        self.status_label.pack()
        
        # Audio level display
        audio_frame = tk.Frame(main_frame, bg='#1a1a1a')
        audio_frame.pack(fill='x', pady=5)
        
        tk.Label(audio_frame, text="Audio:", fg='#cccccc', bg='#1a1a1a').pack(side='left')
        self.audio_bar = ttk.Progressbar(audio_frame, length=150, mode='determinate')
        self.audio_bar.pack(side='right', padx=(5, 0))
        
        # Timer display
        self.timer_label = tk.Label(main_frame, text="Timer: --", 
                                  fg='#ffaa00', bg='#1a1a1a')
        self.timer_label.pack(pady=5)
        
        # Cycle counter
        self.cycle_label = tk.Label(main_frame, text="Cycle: 0", 
                                  fg='#00aaff', bg='#1a1a1a')
        self.cycle_label.pack()
        
        # Control hints
        hints_frame = tk.Frame(main_frame, bg='#1a1a1a')
        hints_frame.pack(fill='x', pady=(10, 0))
        
        tk.Label(hints_frame, text="Controls:", fg='#cccccc', bg='#1a1a1a', 
                font=('Arial', 8)).pack()
        tk.Label(hints_frame, text="SPACE: Confirm | ESC: Exit", 
                fg='#888888', bg='#1a1a1a', font=('Arial', 7)).pack()
        
        # Close button (small X in corner)
        close_btn = tk.Button(main_frame, text="×", command=self.close_overlay,
                            fg='#ff4444', bg='#1a1a1a', bd=0,
                            font=('Arial', 12, 'bold'))
        close_btn.place(relx=1.0, rely=0.0, anchor='ne')
        
    def setup_ipc(self):
        """Setup Inter-Process Communication"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('localhost', 12345))
            self.socket.listen(1)
            print("✅ IPC server started on port 12345")
        except Exception as e:
            print(f"⚠️ IPC setup failed: {e}")
            self.socket = None
    
    def listen_for_updates(self):
        """Listen for status updates from the main voice control script"""
        if not self.socket:
            return
            
        while True:
            try:
                client, addr = self.socket.accept()
                data = client.recv(1024).decode('utf-8')
                if data:
                    update = json.loads(data)
                    self.update_display(update)
                client.close()
            except Exception as e:
                print(f"IPC error: {e}")
                time.sleep(1)
    
    def update_display(self, update):
        """Update the display with new status information"""
        self.current_state.update(update)
        
        # Update UI elements in main thread
        self.window.after(0, self._update_ui)
    
    def _update_ui(self):
        """Update UI elements (must be called from main thread)"""
        state = self.current_state
        
        # Update status text and color
        if state['recording']:
            self.status_label.config(text="🎤 Recording...", fg='#ff4444')
        elif state['confirming']:
            self.status_label.config(text="⌛ Confirming...", fg='#ffaa00')
        else:
            self.status_label.config(text="✅ Ready", fg='#00ff88')
        
        # Update audio level bar
        audio_percent = min(state['audio_level'] * 1000, 100)  # Scale appropriately
        self.audio_bar['value'] = audio_percent
        
        # Update timer
        if state['timer'] > 0:
            self.timer_label.config(text=f"Timer: {state['timer']:.1f}s")
        else:
            self.timer_label.config(text="Timer: --")
        
        # Update cycle count
        self.cycle_label.config(text=f"Cycle: {state['cycle']}")
    
    def start_move(self, event):
        """Start moving the window"""
        self.x = event.x
        self.y = event.y
    
    def do_move(self, event):
        """Move the window"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")
    
    def close_overlay(self):
        """Close the overlay window"""
        if self.socket:
            self.socket.close()
        self.window.destroy()
    
    def run(self):
        """Start the overlay"""
        print("🖥️ Starting Warp Voice Status Overlay")
        print("   - Drag to move")
        print("   - Click × to close")
        self.window.mainloop()

def main():
    overlay = WarpStatusOverlay()
    overlay.run()

if __name__ == "__main__":
    main()
