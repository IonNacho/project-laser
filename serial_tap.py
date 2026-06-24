#!/usr/bin/env python3
"""serial_tap.py

Read a USB-serial device, append raw lines to CSV, and broadcast copies
to any connected WebSocket clients. Designed to be read-only (non-intrusive).

Usage example:
  python serial_tap.py --port /dev/ttyUSB0 --baud 9600 --csv data.csv --ws-host 0.0.0.0 --ws-port 8765

On Windows use a COM port like `COM3` for `--port`.
"""
import argparse
import asyncio
import csv
import datetime
import threading
import sys

try:
    import serial
except Exception:
    print('Missing dependency: pyserial. See requirements.txt')
    raise

try:
    import websockets
except Exception:
    print('Missing dependency: websockets. See requirements.txt')
    raise


connected_clients = set()


async def ws_handler(websocket, path):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)


async def broadcast_message(message: str):
    if not connected_clients:
        return
    webs = list(connected_clients)
    await asyncio.wait([ws.send(message) for ws in webs])


def serial_reader_loop(port: str, baud: int, csv_path: str, loop: asyncio.AbstractEventLoop):
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as e:
        print(f'Error opening serial port {port}:', e)
        return

    # Ensure CSV has header if new
    try:
        f = open(csv_path, 'a', newline='', encoding='utf-8')
    except Exception as e:
        print('Error opening CSV file:', e)
        ser.close()
        return

    writer = csv.writer(f)
    try:
        if f.tell() == 0:
            writer.writerow(['timestamp_utc', 'raw_line'])
            f.flush()

        while True:
            try:
                raw = ser.readline()
            except Exception as e:
                print('Serial read error:', e)
                break
            if not raw:
                continue
            try:
                text = raw.decode('utf-8', errors='replace').strip()
            except Exception:
                text = str(raw)
            ts = datetime.datetime.utcnow().isoformat() + 'Z'
            writer.writerow([ts, text])
            f.flush()
            # send to websocket clients via the asyncio loop
            asyncio.run_coroutine_threadsafe(broadcast_message(f'{ts} {text}'), loop)
    finally:
        try:
            f.close()
        except Exception:
            pass
        try:
            ser.close()
        except Exception:
            pass


def parse_args():
    p = argparse.ArgumentParser(description='Serial tap: log and broadcast serial output')
    p.add_argument('--port', required=True, help='Serial port path (e.g. /dev/ttyUSB0 or COM3)')
    p.add_argument('--baud', type=int, default=9600, help='Baud rate (default 9600)')
    p.add_argument('--csv', default='data.csv', help='CSV output file (default data.csv)')
    p.add_argument('--ws-host', default='0.0.0.0', help='WebSocket host to bind (default 0.0.0.0)')
    p.add_argument('--ws-port', type=int, default=8765, help='WebSocket port (default 8765)')
    return p.parse_args()


def main():
    args = parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    start_server = websockets.serve(ws_handler, args.ws_host, args.ws_port)
    server = loop.run_until_complete(start_server)

    # Start serial reader in a background thread
    t = threading.Thread(target=serial_reader_loop, args=(args.port, args.baud, args.csv, loop), daemon=True)
    t.start()

    print(f'WebSocket server listening on ws://{args.ws_host}:{args.ws_port}/')
    print(f'Reading serial on {args.port} @ {args.baud} baud and appending to {args.csv}')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Shutting down...')
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.stop()


if __name__ == '__main__':
    main()
