#!/usr/bin/env python3
import sys
import datetime

def main():
    logfile = 'scans.log'
    print("Listening for scanner input. Focus this terminal and scan; Ctrl+C to stop.")
    try:
        with open(logfile, 'a', encoding='utf-8') as f:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                s = line.strip()
                if s:
                    ts = datetime.datetime.utcnow().isoformat() + 'Z'
                    f.write(f'{ts}\t{s}\n')
                    f.flush()
                    print(f'[{ts}] {s}')
    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == '__main__':
    main()
