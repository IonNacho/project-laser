#!/usr/bin/env python3
"""Simple WebSocket client to display messages from serial_tap.py

Usage:
  python ws_client.py --host 192.168.1.42 --port 8765
"""
import argparse
import asyncio

try:
    import websockets
except Exception:
    print('Missing dependency: websockets. See requirements.txt')
    raise


async def run(host: str, port: int):
    uri = f'ws://{host}:{port}/'
    print('Connecting to', uri)
    try:
        async with websockets.connect(uri) as ws:
            print('Connected — waiting for messages...')
            async for msg in ws:
                print(msg)
    except Exception as e:
        print('Connection error:', e)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--host', required=True, help='WebSocket host or IP')
    p.add_argument('--port', type=int, default=8765, help='WebSocket port (default 8765)')
    return p.parse_args()


def main():
    args = parse_args()
    asyncio.run(run(args.host, args.port))


if __name__ == '__main__':
    main()
