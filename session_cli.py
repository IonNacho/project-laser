#!/usr/bin/env python3
"""Interactive CLI session to collect operator, lot, and equipment scans.

Saves a JSON record per session to `sessions.jsonl` and appends raw lines to `scans.log`.
"""
import json
import uuid
import datetime
import os
from parser import parse_scan


def utc_now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


EQUIP_PROMPTS = [
    ("eq_indicator", "Scan digital force indicator (EQ0155-01) or type value:"),
    ("eq_stand", "Scan force test stand (EQ0155-03) or type value:"),
    ("load_cell", "Scan load cell (EQ0155-05-A/B) or type value:"),
]


def save_raw(raw: str):
    with open('scans.log', 'a', encoding='utf-8') as f:
        f.write(raw.rstrip('\n') + '\n')


def save_session(rec: dict):
    with open('sessions.jsonl', 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec) + '\n')


def prompt_input(prompt: str) -> str:
    v = input(prompt + ' ').strip()
    return v


def collect_session():
    print('--- New FM6 session (development mode) ---')
    operator = prompt_input('Operator name (type and press Enter):')
    ts = utc_now_iso()

    # Lot
    lot = prompt_input('Scan or type Lot number (e.g. M00207):')
    save_raw(f'{ts}\tLOT\t{lot}')

    equipment = {}
    raw_scans = []
    parsed = {}
    for key, prompt in EQUIP_PROMPTS:
        v = prompt_input(prompt)
        raw_scans.append(v)
        save_raw(f'{utc_now_iso()}\t{v}')
        parsed_v = parse_scan(v)
        equipment[key] = parsed_v.get('code') or v
        parsed[key] = parsed_v

    rec = {
        'session_id': str(uuid.uuid4()),
        'operator': operator,
        'timestamp': ts,
        'lot': lot,
        'equipment': equipment,
        'parsed': parsed,
        'raw_scans': raw_scans,
    }
    save_session(rec)
    print('Session saved:', rec['session_id'])
    print(json.dumps(rec, indent=2))


def main():
    os.makedirs(os.path.dirname(os.path.abspath('sessions.jsonl')), exist_ok=True)
    try:
        while True:
            collect_session()
            cont = input('Start another session? (y/n) ').strip().lower()
            if cont != 'y':
                break
    except KeyboardInterrupt:
        print('\nExiting.')


if __name__ == '__main__':
    main()
