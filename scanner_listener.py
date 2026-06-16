#!/usr/bin/env python3
import sys
import datetime
import select
import time


def utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    logfile = 'scans.log'
    print("Listening for scanner input. Focus this terminal and scan; Ctrl+C to stop.")
    buf = ''
    last_input_time = None
    flush_timeout = 0.25  # seconds of inactivity to treat buffer as complete
    try:
        with open(logfile, 'a', encoding='utf-8') as f:
            while True:
                rlist, _, _ = select.select([sys.stdin], [], [], flush_timeout)
                if rlist:
                    c = sys.stdin.read(1)
                    if not c:
                        break
                    if c in ('\n', '\r'):
                        s = buf.strip()
                        buf = ''
                        if s:
                            ts = utc_now_iso() + 'Z'
                            f.write(f'{ts}\t{s}\n')
                            f.flush()
                            print(f'[{ts}] {s}')
                        last_input_time = None
                    else:
                        buf += c
                        last_input_time = time.time()
                else:
                    # timeout occurred; if buffer has content and enough idle time passed, flush it
                    if buf and last_input_time and (time.time() - last_input_time) >= flush_timeout:
                        s = buf.strip()
                        buf = ''
                        if s:
                            ts = utc_now_iso() + 'Z'
                            f.write(f'{ts}\t{s}\n')
                            f.flush()
                            print(f'[{ts}] {s}')
                        last_input_time = None
    except KeyboardInterrupt:
        print("Stopped.")


if __name__ == '__main__':
    main()
