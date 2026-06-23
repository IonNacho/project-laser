#!/usr/bin/env python3
"""Minimal web scanner app — simple scan input for lot number.

Run on the Pi and open http://<pi-ip>:8000

Features:
- Single page with a focused text input for scanner keyboard wedge
- Posts to /scan, saves to `sessions_minimal.jsonl`
"""
from flask import Flask, request, jsonify, render_template_string
import datetime, json, os, re

app = Flask(__name__)

SESS_FILE = 'sessions_minimal.jsonl'

# mapping M00 -> test type
TEST_MAP = {
  'M00124': 'Blister pack',
  'M00120': 'Header/Retainer caps',
  'M00123': 'Feed through Pin',
  'M00207': 'Battery weld',
  'M00121': 'Strap weld',
}

HTML = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Simple Scan</title>
  <style>body{font-family:Arial;margin:20px}label{display:block;margin-top:8px}</style>
</head>
<body>
  <h2>Scan Lot — Simple</h2>
  <p>Focus the box and scan the lot you are working on.</p>
  <input id="scan" autofocus style="width:60%" placeholder="Scan here or type...">
  <button id="btn">Submit</button>
  <div id="info" style="margin-top:12px;color:green"></div>

  <script>
    const input = document.getElementById('scan');
    const btn = document.getElementById('btn');
    const info = document.getElementById('info');
    function post(text){
      fetch('/scan', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({text:text})})
        .then(r=>r.json()).then(j=>{
          info.innerText = 'Saved session: '+j.session_id+' (lot:'+ (j.lot||'') +')';
          input.value=''; input.focus();
        }).catch(e=>{ info.style.color='red'; info.innerText='Error: '+e });
    }
    btn.addEventListener('click', ()=> post(input.value));
    input.addEventListener('keydown', (e)=>{ if(e.key==='Enter') post(input.value); });
  </script>
</body>
</html>
'''


def save_session(lot, raw, m00='', test_type=''):
  rec = {
    'session_id': datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'),
    'lot': lot,
    'raw': raw,
    'm00': m00,
    'test_type': test_type,
    'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  }
    try:
        with open(SESS_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec) + '\n')
    except Exception:
        pass
    return rec


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/scan', methods=['POST'])
def scan():
    js = request.get_json(force=True)
    text = (js.get('text') or '').strip()
  # parse lot starting with LN (e.g. LN12345 or LN:12345)
  lot = ''
  m = re.search(r'\bLN[:\s-]*([A-Za-z0-9-]+)\b', text, re.IGNORECASE)
  if m:
    lot = m.group(1)
  else:
    # fallback: find first token that is not an M00 code and looks like a lot
    parts = re.split(r'\s|,|;|\||\(|\)', text)
    parts = [p for p in parts if p]
    lot_candidate = ''
    for p in parts:
      if re.match(r'(?i)^M00\d{3}$', p):
        continue
      # ignore short tokens like 'LN' alone
      if len(p) >= 3:
        lot_candidate = p
        break
    if lot_candidate:
      lot = lot_candidate

  # find M00 code
  m00 = ''
  mm = re.search(r'\b(M00\d{3})\b', text, re.IGNORECASE)
  if mm:
    m00 = mm.group(1).upper()
  test_type = TEST_MAP.get(m00, '')

  rec = save_session(lot, text, m00=m00, test_type=test_type)
    return jsonify(rec)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
