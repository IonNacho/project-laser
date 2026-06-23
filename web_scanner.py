#!/usr/bin/env python3
"""Web scanner interface for FM6 entry.

Run on the Pi and open http://<pi-ip>:5000 from another device on the same network.

Features:
- Simple single-page UI that auto-focuses a scan input box
- Parses scanned text for M00*, Rev, Lot, Exp date
- Maps M00 codes to test types using the provided chart
- Saves records to `scans_web.jsonl` and `scans_web.csv`
"""
from flask import Flask, request, jsonify, render_template_string
import re
import json
import csv
import os
import datetime

app = Flask(__name__)

JSONL = 'scans_web.jsonl'
CSV = 'scans_web.csv'

# mapping provided by user
TEST_MAP = {
    'M00124': 'Blister Pack/ Tray seal',
    'M00120': 'Header',
    'M00123': 'Feed Through pins',
    'M00207': 'Battery weld',
    'M00121': 'Strap weld',
}

INDEX_HTML = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Project Laser — Scan</title>
  <style>body{font-family:Arial;margin:20px}label{display:block;margin-top:8px}#result{margin-top:12px;padding:8px;border:1px solid #ddd}</style>
</head>
<body>
  <h2>Scan Lot (focus input and scan)</h2>
  <input id="scan" autofocus style="width:80%" placeholder="Scan here or type..."> 
  <button id="btn">Submit</button>
  <div id="result"></div>

  <script>
    const input = document.getElementById('scan');
    const btn = document.getElementById('btn');
    const result = document.getElementById('result');
    function post(text){
      fetch('/scan', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text:text})})
        .then(r=>r.json()).then(j=>{
          result.innerHTML = '<pre>'+JSON.stringify(j,null,2)+'</pre>';
          input.value = '';
          input.focus();
        }).catch(e=>{ result.innerText = 'Error: '+e });
    }
    btn.addEventListener('click', ()=> post(input.value));
    input.addEventListener('keydown', (e)=>{ if(e.key==='Enter') post(input.value); });
  </script>
</body>
</html>
'''


def parse_scan(text):
    # try to find M00 code, Rev, Lot, Exp
    t = text.strip()
    out = {'raw': t, 'm00': '', 'rev': '', 'lot': '', 'exp': ''}
    m = re.search(r'\b(M00\d+)\b', t, re.IGNORECASE)
    if m:
        out['m00'] = m.group(1).upper()
    r = re.search(r'\bRev[:\s-]*([A-Za-z0-9]+)\b', t, re.IGNORECASE)
    if r:
        out['rev'] = r.group(1)
    l = re.search(r'\bLot[:\s-]*([A-Za-z0-9-]+)\b', t, re.IGNORECASE)
    if l:
        out['lot'] = l.group(1)
    # expiry date common patterns
    e = re.search(r'\b(20\d{2}-\d{2}-\d{2})\b', t)
    if not e:
        e = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', t)
    if e:
        out['exp'] = e.group(1)

    # fallback: split by whitespace and try to assign
    if not (out['m00'] and out['lot']):
        parts = re.split(r'\s|,|;|\||\(|\)', t)
        parts = [p for p in parts if p]
        for p in parts:
            up = p.upper()
            if up.startswith('M00') and not out['m00']:
                out['m00'] = up
            if up.lower().startswith('rev') and not out['rev']:
                out['rev'] = up.split('rev')[-1].strip()
            if p.isalnum() and not out['lot'] and len(p) >= 3:
                out['lot'] = p
    return out


def record_and_save(rec):
    # append JSONL
    with open(JSONL, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec) + '\n')
    # append CSV header if needed
    cols = ['timestamp','raw','m00','rev','lot','exp','test_type']
    exists = os.path.exists(CSV)
    with open(CSV, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if not exists:
            w.writeheader()
        w.writerow({k: rec.get(k,'') for k in cols})


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


@app.route('/scan', methods=['POST'])
def scan():
    js = request.get_json(force=True)
    text = js.get('text','')
    parsed = parse_scan(text)
    parsed['timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    parsed['test_type'] = TEST_MAP.get(parsed.get('m00',''), 'Unknown')
    record_and_save({
        'timestamp': parsed['timestamp'],
        'raw': parsed['raw'],
        'm00': parsed['m00'],
        'rev': parsed['rev'],
        'lot': parsed['lot'],
        'exp': parsed['exp'],
        'test_type': parsed['test_type'],
    })
    return jsonify(parsed)


if __name__ == '__main__':
    # bind to all interfaces so other devices on LAN can connect
    app.run(host='0.0.0.0', port=5000, debug=False)
