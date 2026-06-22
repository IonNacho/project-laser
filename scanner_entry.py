#!/usr/bin/env python3
"""Small scanner entry GUI: focus the box, scan a code, app logs it to scans.log.

Designed for keyboard-wedge scanners. Captures input on Enter or after a short idle.
"""
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import datetime
import time


def utc_now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class ScannerEntryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Scanner Entry')
        self.geometry('640x240')

        tk.Label(self, text='Focus the box below and scan a code').pack(anchor='w', padx=8, pady=(8,0))
        self.entry = tk.Entry(self, font=('Consolas', 14))
        self.entry.pack(fill='x', padx=8, pady=6)
        self.entry.focus_set()

        self.entry.bind('<Return>', self.on_enter)
        self.entry.bind('<Key>', self.on_key)

        self.logview = ScrolledText(self, height=8, state='disabled', font=('Consolas', 12))
        self.logview.pack(fill='both', expand=True, padx=8, pady=(0,8))

        self.buf_timer = None
        self.flush_delay = 250  # ms

    def log(self, s: str):
        ts = utc_now_iso() + 'Z'
        line = f'[{ts}] {s}\n'
        # UI
        self.logview.configure(state='normal')
        self.logview.insert('end', line)
        self.logview.see('end')
        self.logview.configure(state='disabled')
        # file
        try:
            with open('scans.log', 'a', encoding='utf-8') as f:
                f.write(f'{ts}\t{s}\n')
        except Exception:
            pass

    def submit(self):
        s = self.entry.get().strip()
        if not s:
            return
        self.log(s)
        self.entry.delete(0, 'end')
        self.entry.focus_set()

    def on_enter(self, event=None):
        self.cancel_timer()
        self.submit()

    def on_key(self, event=None):
        # schedule a flush in case device doesn't send Enter
        self.cancel_timer()
        self.buf_timer = self.after(self.flush_delay, self.submit)

    def cancel_timer(self):
        if self.buf_timer:
            try:
                self.after_cancel(self.buf_timer)
            except Exception:
                pass
            self.buf_timer = None


def main():
    app = ScannerEntryApp()
    app.mainloop()


if __name__ == '__main__':
    main()
