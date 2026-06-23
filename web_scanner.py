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
import uuid

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
    <style>
        body{font-family:Arial;margin:20px}
        label{display:block;margin-top:8px}
        #result{margin-top:12px;padding:8px;border:1px solid #ddd}
        table{border-collapse:collapse}
        td,th{padding:6px;border:1px solid #ddd}
        #fields{margin-top:12px}
    </style>
    </head>
<body>
    <h2>Scan Lot (focus input and scan)</h2>
    <input id="scan" autofocus style="width:80%" placeholder="Scan here or type..."> 
    <button id="btn">Submit</button>

    <div id="fields" style="display:none">
        <h3>Parsed</h3>
        <table>
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td>M00</td><td id="f_m00"></td></tr>
            <tr><td>Lot</td><td id="f_lot"></td></tr>
            <tr><td>Rev</td><td id="f_rev"></td></tr>
            <tr><td>Exp</td><td id="f_exp"></td></tr>
            <tr><td>Test Type</td><td id="f_type"></td></tr>
        </table>
        <div style="margin-top:8px">
            <button id="start">Start Session</button>
            <span id="session_info" style="margin-left:12px"></span>
        </div>
    </div>

    <div id="result"></div>

    <script>
        const input = document.getElementById('scan');
        const btn = document.getElementById('btn');
        const result = document.getElementById('result');
        const fields = document.getElementById('fields');
        const startBtn = document.getElementById('start');
        const sessionInfo = document.getElementById('session_info');
        let idleTimer = null;
        let lastParsed = null;

        function showParsed(j){
            lastParsed = j;
            document.getElementById('f_m00').innerText = j.m00 || '';
            document.getElementById('f_lot').innerText = j.lot || '';
            document.getElementById('f_rev').innerText = j.rev || '';
            document.getElementById('f_exp').innerText = j.exp || '';
            document.getElementById('f_type').innerText = j.test_type || 'Unknown';
            fields.style.display = 'block';
            result.innerText = '';
        }

        function postScan(text){
            fetch('/scan', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text:text})})
                .then(r=>r.json()).then(j=>{
                    showParsed(j);
                    // auto-start session if lot present
                    if(j.lot){
                        startSession(j);
                    }
                    input.value = '';
                    input.focus();
                }).catch(e=>{ result.innerText = 'Error: '+e });
        }

        function startSession(data){
            // disable button while creating
            startBtn.disabled = true;
            fetch('/session', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data)})
                .then(r=>r.json()).then(s=>{
                    sessionInfo.innerText = 'Session: '+s.session_id+' (lot '+(s.lot||'')+')';
                    startBtn.disabled = false;
                }).catch(e=>{ sessionInfo.innerText = 'Session error'; startBtn.disabled=false});
        }

        btn.addEventListener('click', ()=> postScan(input.value));
        startBtn.addEventListener('click', ()=>{ if(lastParsed) startSession(lastParsed); });

        // auto-submit after idle 200ms
        input.addEventListener('input', ()=>{
            if(idleTimer) clearTimeout(idleTimer);
            idleTimer = setTimeout(()=>{ postScan(input.value); }, 200);
        });
        input.addEventListener('keydown', (e)=>{ if(e.key==='Enter') postScan(input.value); });
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


SESSIONS_FILE = 'sessions_web.jsonl'


@app.route('/session', methods=['POST'])
def session_create():
    js = request.get_json(force=True)
    lot = js.get('lot', '')
    m00 = js.get('m00', '')
    test_type = js.get('test_type', TEST_MAP.get(m00, 'Unknown'))
    session_id = uuid.uuid4().hex
    rec = {
        'session_id': session_id,
        'lot': lot,
        'm00': m00,
        'test_type': test_type,
        'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    # append
    with open(SESSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec) + '\n')
    # also write a prefill file for the FM6 GUI to pick up
    try:
        prefill = {
            'lot': lot,
            'm00': m00,
            'test_type': test_type,
            'rev': js.get('rev',''),
            'exp': js.get('exp',''),
            'timestamp': rec['started_at']
        }
        with open('fm6_prefill.json.tmp', 'w', encoding='utf-8') as pf:
            json.dump(prefill, pf)
        # atomically move into place
        os.replace('fm6_prefill.json.tmp', 'fm6_prefill.json')
    except Exception:
        pass
    return jsonify(rec)


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
