# Warp Voice Control

A voice control system for Warp Terminal that enables hands-free operation with safety features and confirmation controls.

## Features

- **Immediate Voice Detection**: Starts recording as soon as voice is detected
- **Smart Silence Detection**: Automatically stops after 3 seconds of silence
- **Dual Confirmation System**:
  - Manual confirmation with SPACE key
  - Automatic confirmation after 10 seconds of silence
  - Continue speaking to cancel confirmation
- **Safety Features**:
  - Quick-cancel by speaking
  - Emergency stop with ESC
  - Window focus protection
  - Audio device verification

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/warp-voice-control.git
cd warp-voice-control
```

2. Run the setup script:
```bash
./setup_warp_voice.sh
```

3. Start a new terminal or reload your bash configuration:
```bash
source ~/.bashrc
```

## Usage

1. Open Warp Terminal
2. Open a separate terminal
3. Run:
```bash
warpvoice
```

### Controls

- **Speaking**: Automatically starts recording
- **Silence (3s)**: Stops recording
- **SPACE**: Manually confirm and send
- **Wait (10s)**: Automatically confirm and send
- **Speak Again**: Cancel confirmation and continue
- **ESC**: Emergency stop

## Requirements

- Python 3.6+
- Warp Terminal
- Linux with X11
- Python packages:
  - pyaudio
  - numpy
  - pyautogui
  - pynput

## Configuration

Settings are stored in `~/.warp_controller_config.json`

## License

MIT License
