#!/bin/sh
# Create a Desktop launcher for the scanner entry app on Raspberry Pi
cat > "$HOME/Desktop/ProjectLaser-scanner.desktop" <<'EOF'
[Desktop Entry]
Name=Project Laser Scanner
Comment=Run scanner entry GUI
Exec=python3 /home/pi/project-laser/scanner_entry.py
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
EOF
chmod +x "$HOME/Desktop/ProjectLaser-scanner.desktop"
echo "Created $HOME/Desktop/ProjectLaser-scanner.desktop"
