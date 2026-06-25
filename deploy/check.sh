#!/usr/bin/env bash
# deploy/check.sh
# Verify presence of files expected on the Raspberry Pi deploy target

set -euo pipefail

TARGET_DIR="${1:-/home/pi/project-laser}"
SERVICE_FILE="${2:-serial_tap.service}"

echo "Checking deploy target: $TARGET_DIR"

missing=0

check() {
    path="$1"
    desc="$2"
    if [[ -e "$TARGET_DIR/$path" ]]; then
        echo "OK: $desc -> $path"
    else
        echo "MISSING: $desc -> $path"
        missing=1
    fi
}

# Files we expect in a minimal deploy
check "serial_tap.py" "main serial reader script"
check "requirements.txt" "Python dependencies file"
check "web_ui" "web UI directory (static files)"
check "$SERVICE_FILE" "systemd service file"

echo
echo "Inspecting root service file (if present locally)"
if [[ -f "$SERVICE_FILE" ]]; then
    echo "--- $SERVICE_FILE ---"
    sed -n '1,200p' "$SERVICE_FILE"
    echo "---------------------"
else
    echo "No local $SERVICE_FILE found."
fi

if [[ $missing -ne 0 ]]; then
    echo
    echo "One or more expected files are missing from $TARGET_DIR."
    echo "Suggested action: copy only the listed OK files into the Pi or adjust the paths in the service file."
    exit 2
else
    echo
    echo "All minimal files present in $TARGET_DIR (according to this checklist)."
    exit 0
fi
