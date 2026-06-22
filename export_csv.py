#!/usr/bin/env python3
"""Export sessions.jsonl to CSV for external use."""
import json
import csv
import sys


def export(infile='sessions.jsonl', outfile='sessions_export.csv'):
    with open(infile, 'r', encoding='utf-8') as inf, open(outfile, 'w', newline='', encoding='utf-8') as outf:
        writer = csv.writer(outf)
        header = ['session_id', 'operator', 'timestamp', 'lot', 'eq_indicator', 'eq_stand', 'load_cell']
        writer.writerow(header)
        for line in inf:
            rec = json.loads(line)
            eq = rec.get('equipment', {})
            row = [rec.get('session_id'), rec.get('operator'), rec.get('timestamp'), rec.get('lot'), eq.get('eq_indicator'), eq.get('eq_stand'), eq.get('load_cell')]
            writer.writerow(row)
    print('Wrote', outfile)


if __name__ == '__main__':
    infile = sys.argv[1] if len(sys.argv) > 1 else 'sessions.jsonl'
    outfile = sys.argv[2] if len(sys.argv) > 2 else 'sessions_export.csv'
    export(infile, outfile)
