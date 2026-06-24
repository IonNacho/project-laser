# serial_tap usage

This script reads a serial device, appends each raw line to a CSV file, and broadcasts copies to connected WebSocket clients.

Quick start (on the Pi):

```bash
python3 -m pip install -r requirements.txt
python3 serial_tap.py --port /dev/ttyUSB0 --baud 9600 --csv data.csv --ws-host 0.0.0.0 --ws-port 8765
```

On Windows use a COM port name for `--port`, e.g. `COM3`.

Client consumption examples:
- From a browser, open a WebSocket to `ws://<pi-ip>:8765/` and listen for text messages.
- From another Python process you can use `websockets` or any WebSocket client library.

Notes:
- The script is intentionally read-only: it opens the serial device for reading and never writes to it.
- When you add a passive RS-232 tee tomorrow, point `--port` to the Pi's serial adapter and it will record the same stream the PC receives.

Systemd service (optional)
 - A sample systemd unit `serial_tap.service` is included for running the tap on boot.
 - To install the service on a Raspberry Pi, run the included installer as root from the repo root:

```bash
sudo bash install_serial_tap.sh
```

 - The installer copies the repository to `/opt/project-laser`, installs Python deps, creates `/var/log/serial_tap`, and enables the `serial_tap.service` unit.

Service configuration notes:
 - Edit `serial_tap.service` to change the `ExecStart` port, baud, CSV path, or user.
 - After editing the unit file, reload systemd with `sudo systemctl daemon-reload` and restart the service.

