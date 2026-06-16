#!/usr/bin/env python3
"""Simple GUI scanner listener using Tkinter.

Focus this window and scan codes. Scanned data will appear in the window
and be appended to `scans.log` in the same folder.
"""
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import datetime
import time


def utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class ScannerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Scanner Listener')
        self.geometry('640x360')
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        self.text = ScrolledText(self, state='disabled', wrap='none', font=('Consolas', 12))
        self.text.pack(fill='both', expand=True)

        self.status = tk.Label(self, text='Focus this window and scan a code...', anchor='w')
        self.status.pack(fill='x')

        self.buf = ''
        self.last_input_time = None
        self.flush_delay = 250  # ms
        self.after_id = None

        # Bind to key events when window has focus
        self.bind_all('<Key>', self.on_key)

    def log(self, s: str):
        ts = utc_now_iso() + 'Z'
        line = f'[{ts}] {s}\n'
        # append to text widget
        self.text.configure(state='normal')
        self.text.insert('end', line)
        self.text.see('end')
        self.text.configure(state='disabled')
        # append to log file
        try:
            with open('scans.log', 'a', encoding='utf-8') as f:
                f.write(f'{ts}\t{s}\n')
        except Exception as e:
            print('Failed to write log:', e)

    def flush_buffer(self):
        if self.buf:
            s = self.buf.strip()
            self.buf = ''
            if s:
                self.log(s)
        self.after_id = None

    def schedule_flush(self):
        if self.after_id:
            self.after_cancel(self.after_id)
        self.after_id = self.after(self.flush_delay, self.flush_buffer)

    def on_key(self, event):
        # Ignore modifier keys
        if len(event.keysym) > 1 and event.keysym not in ('Return', 'BackSpace'):
            return
        ch = event.char
        if ch in ('\r', '\n') or event.keysym == 'Return':
            # newline -> flush
            self.flush_buffer()
            return
        if event.keysym == 'BackSpace':
            self.buf = self.buf[:-1]
            return
        if ch:
            self.buf += ch
            self.last_input_time = time.time()
            self.schedule_flush()

    def on_close(self):
        # flush any pending
        if self.after_id:
            self.after_cancel(self.after_id)
        self.flush_buffer()
        self.destroy()


def main():
    app = ScannerGUI()
    app.mainloop()


if __name__ == '__main__':
    main()
