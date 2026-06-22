"""Simple parser for scanned strings.

Functions:
 - parse_scan(text): return dict with keys: code, desc, date, raw

This parser is forgiving and uses simple regexes to extract an equipment/code token
and a date in formats like 20-Oct-26, 01-Jan-50, 14-10-2026, etc.
"""
from typing import Optional, Dict
import re
import datetime


CODE_RE = re.compile(r"([A-Z]{1,5}\d{1,6}(?:-[A-Z0-9]+)?)")
DATE_RE = re.compile(r"(\b\d{1,2}[-/][A-Za-z]{3}[-/]\d{2,4}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b)")


def _parse_date(s: str) -> Optional[str]:
    s = s.strip()
    # Try several formats
    fmts = ["%d-%b-%y", "%d-%b-%Y", "%d/%b/%y", "%d/%m/%y", "%d/%m/%Y", "%d-%m-%Y"]
    for f in fmts:
        try:
            dt = datetime.datetime.strptime(s, f)
            return dt.date().isoformat()
        except Exception:
            continue
    # try parsing year-only like Jan-50 not covered; return None
    return None


def parse_scan(text: str) -> Dict:
    """Parse a scanned text into structured fields.

    Returns a dict: { 'raw': text, 'code':str|None, 'desc':str|None, 'date':ISO|None }
    """
    if not text:
        return {"raw": "", "code": None, "desc": None, "date": None}
    txt = text.strip()
    code_m = CODE_RE.search(txt)
    date_m = DATE_RE.search(txt)
    code = code_m.group(1) if code_m else None
    date_iso = None
    if date_m:
        date_iso = _parse_date(date_m.group(1))
    # description: remove code and date
    desc = txt
    if code:
        desc = re.sub(re.escape(code), '', desc, count=1).strip()
    if date_m:
        desc = desc.replace(date_m.group(1), '').strip(' -:')
    desc = desc if desc else None
    return {"raw": txt, "code": code, "desc": desc, "date": date_iso}


if __name__ == '__main__':
    # quick manual test
    samples = [
        "EQ0155-03 CAL DUE DATE 14-Oct-26",
        "Q0155-A CAL DUE DATE 20-Oct-26",
        "M00120 RevD LN14855 Exp 01-Jan-50",
    ]
    for s in samples:
        print(s, '->', parse_scan(s))
