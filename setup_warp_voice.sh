#!/bin/bash

echo "=== Warp Voice Control Setup ==="
echo "Installing components and creating launcher..."

# Create program directory
mkdir -p ~/.warp-voice

# Copy main script
cp warp_quick_start.py ~/.warp-voice/
chmod +x ~/.warp-voice/warp_quick_start.py

# Create the launcher alias in bashrc (if not exists)
if ! grep -q "alias warpvoice=" ~/.bashrc; then
    echo "# Warp Voice Control" >> ~/.bashrc
    echo "alias warpvoice='python3 ~/.warp-voice/warp_quick_start.py'" >> ~/.bashrc
fi

# Create README
cat > ~/.warp-voice/README.md << 'EOF'
# Warp Voice Control

Quick voice control for Warp Terminal with safety features.

## Usage
Run `warpvoice` in any terminal (not Warp).

## Features
- Immediate voice detection
- Auto-stops after 3s silence
- Manual (SPACE) or automatic (10s) confirmation
- Continue speaking to cancel confirmation
- ESC to exit

## Controls
- SPACE: Confirm input manually
- ESC: Emergency stop
- Speaking: Starts recording automatically

## Configuration
Settings stored in: ~/.warp_controller_config.json

## Safety Features
- Dual confirmation system
- Quick cancel by speaking
- Emergency stop with ESC
EOF

echo ""
echo "✅ Installation complete!"
echo ""
echo "To start using:"
echo "1. Open a new terminal or run: source ~/.bashrc"
echo "2. Type 'warpvoice' to start"
echo ""
echo "Configuration saved in: ~/.warp-voice/"
echo "Type 'cat ~/.warp-voice/README.md' for help"
