#!/usr/bin/env bash
# deploy_to_pi.sh
# Run on the Raspberry Pi to update system packages, install Python tooling,
# ensure pyserial is available, add the local user to dialout, and clone/pull
# the project repository.

set -euo pipefail

REPO_URL="https://github.com/IonNacho/project-laser.git"
# Prefer the babypi1 home if it exists (common on your Pi), else fall back to /home/pi
DEFAULT_TARGET_USER_DIR="/home/babypi1"
if [[ -d "$DEFAULT_TARGET_USER_DIR" ]]; then
    TARGET_DIR="$DEFAULT_TARGET_USER_DIR/project-laser"
else
    TARGET_DIR="/home/pi/project-laser"
fi
BRANCH="main"
REBOOT=false

usage() {
    cat <<EOF
Usage: $0 [--repo URL] [--target DIR] [--branch BRANCH] [--reboot]

Defaults:
  --repo   $REPO_URL
  --target $TARGET_DIR
  --branch $BRANCH

This script must be run on the Raspberry Pi (or via SSH). It will use sudo
for package installs and to modify group membership. If run with sudo, the
original user is detected and added to the 'dialout' group.
EOF
}

while [[ ${#} -gt 0 ]]; do
    case "$1" in
        --repo) REPO_URL="$2"; shift 2;;
        --target) TARGET_DIR="$2"; shift 2;;
        --branch) BRANCH="$2"; shift 2;;
        --reboot) REBOOT=true; shift 1;;
        -h|--help) usage; exit 0;;
        *) echo "Unknown arg: $1"; usage; exit 2;;
    esac
done

# Detect the non-root user if run with sudo
RUN_USER="${SUDO_USER:-${USER:-pi}}"

echo "Starting deploy: repo=$REPO_URL target=$TARGET_DIR branch=$BRANCH user=$RUN_USER"

if [[ $(id -u) -ne 0 ]]; then
    echo "This script should be run with sudo (or as root) to install packages and add groups." >&2
    echo "Re-run with: sudo $0 [--repo ...]" >&2
    exit 1
fi

echo "Updating apt repositories..."
apt update -y

echo "Upgrading packages... (may take several minutes)"
apt upgrade -y

echo "Installing required packages: python3, pip, venv, git"
apt install -y python3 python3-pip python3-venv git

echo "Installing pyserial for python3 (user install)"
# Use the run user's pip to install into their --user site-packages
sudo -u "$RUN_USER" python3 -m pip install --user pyserial

echo "Adding $RUN_USER to dialout group (for serial port access)"
usermod -a -G dialout "$RUN_USER" || true

echo "Cloning or updating repository at $TARGET_DIR"
if [[ -d "$TARGET_DIR/.git" ]]; then
    echo "Repository found, fetching and pulling latest changes..."
    git -C "$TARGET_DIR" fetch --all --prune
    git -C "$TARGET_DIR" checkout "$BRANCH" || true
    git -C "$TARGET_DIR" reset --hard "origin/$BRANCH" || true
    git -C "$TARGET_DIR" pull origin "$BRANCH" || true
else
    echo "Cloning repository into $TARGET_DIR"
    mkdir -p "$(dirname "$TARGET_DIR")"
    git clone --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR"
fi

echo "Fixing ownership of $TARGET_DIR to $RUN_USER"
chown -R "$RUN_USER":"$RUN_USER" "$TARGET_DIR" || true

echo "Deploy complete."

if $REBOOT; then
    echo "Rebooting system to apply group membership changes..."
    reboot
else
    echo "Note: To activate the dialout group for $RUN_USER you must log out/in or reboot."
    echo "Run 'sudo reboot' when convenient to apply the change."
fi

echo "Next steps on the Pi:
  1) Plug in the USB-to-RS232 adapter and run:
       ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true
     or: dmesg | tail -n 40 | grep -i tty
  2) Run the tester without motion:
       python3 $TARGET_DIR/baby/serial_test.py --no-motion --port /dev/ttyUSB0
  3) If OK, run with motion test (ensure area is clear):
       python3 $TARGET_DIR/baby/serial_test.py --port /dev/ttyUSB0
"
