# Deploy README

This folder contains minimal artifacts and checks to deploy the project to a Raspberry Pi.

What to include on the Pi
- `serial_tap.py` — main runtime script that reads serial and broadcasts via WebSocket.
- `requirements.txt` — Python dependencies to install in the Pi venv.
- `web_ui/` — static UI files if the Pi hosts the web UI.
- `serial_tap.service` — systemd unit file (adjust ExecStart and WorkingDirectory to your target path).

Quick deploy steps (on the Pi)

```bash
# clone or update repo
git clone https://github.com/IonNacho/project-laser.git /home/pi/project-laser
cd /home/pi/project-laser

# create venv and install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# install service (edit paths if you used a different target dir)
sudo cp serial_tap.service /etc/systemd/system/serial_tap.service
sudo systemctl daemon-reload
sudo systemctl enable --now serial_tap.service
```

Use `deploy/check.sh` to validate that the target directory contains the minimal files.
