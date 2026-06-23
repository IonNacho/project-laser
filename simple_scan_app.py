#!/usr/bin/env python3
"""Minimal web scanner app — simple scan input for lot number.

Run on the Pi and open http://<pi-ip>:8000

Features:
- Single page with a focused text input for scanner keyboard wedge
- Posts to /scan, saves to `sessions_minimal.jsonl`
"""
from flask import Flask, request, jsonify, render_template_string
import datetime, json, os

app = Flask(__name__)

SESS_FILE = 'sessions_minimal.jsonl'

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


def save_session(lot, raw):
    rec = {
        'session_id': datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'),
        'lot': lot,
        'raw': raw,
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
    # simple heuristic: use whole scanned text as lot
    lot = text
    rec = save_session(lot, text)
    return jsonify(rec)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
