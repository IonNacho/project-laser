#!/usr/bin/env bash
set -euo pipefail

# install_serial_tap.sh
# Copies repository to /opt/project-laser, installs requirements, and
# installs+starts the systemd service. Run on the Pi.

DESTDIR=/opt/project-laser
SERVICE_NAME=serial_tap.service

if [ "$EUID" -ne 0 ]; then
  echo "This script needs to run with sudo to install the service. Re-run with sudo." >&2
  exit 1
fi

echo "Creating destination: $DESTDIR"
mkdir -p "$DESTDIR"
rsync -a --delete --exclude .git ./ "$DESTDIR/"

echo "Installing Python dependencies"
python3 -m pip install -r "$DESTDIR/requirements.txt"

echo "Creating log directory"
mkdir -p /var/log/serial_tap
chown -R pi:pi /var/log/serial_tap || true

echo "Installing systemd service"
cp "$DESTDIR/$SERVICE_NAME" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now $SERVICE_NAME

echo "Done. Service enabled and started. Check status with: systemctl status $SERVICE_NAME"
