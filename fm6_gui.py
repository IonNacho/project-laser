#!/usr/bin/env python3
"""Simple FM6 form GUI.

Left pane shows the FM6 image if available. Right pane has editable fields.
Click a "Capture" button then focus the window and scan the code to fill the field.
Saves filled forms to `fm6_filled.jsonl`.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import datetime
import os
import threading

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

IMAGE_PATH = 'FM6 form.jpeg'


def utc_now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class FM6App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('FM6 Form Helper')
        self.geometry('1000x600')

        self.current_capture_target = None
        self.capture_buffer = ''
        self.capture_timer = None
        self.flush_delay = 250  # ms

        self.create_widgets()

    def create_widgets(self):
        pan = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        pan.pack(fill='both', expand=True)

        left = ttk.Frame(pan, width=600)
        right = ttk.Frame(pan, width=400)
        pan.add(left, weight=3)
        pan.add(right, weight=1)

        # image area
        if PIL_AVAILABLE and os.path.exists(IMAGE_PATH):
            img = Image.open(IMAGE_PATH)
            img = img.resize((600, int(600 * img.height / img.width)), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            lbl = ttk.Label(left, image=self.photo)
            lbl.pack(fill='both', expand=True)
        else:
            ttk.Label(left, text='FM6 form image not available', anchor='center').pack(fill='both', expand=True)

        # right side: form
        frm = right
        ttk.Label(frm, text='FM6 Entry', font=('Helvetica', 14, 'bold')).pack(pady=8)

        self.entries = {}
        fields = [
            ('operator', 'Operator name'),
            ('timestamp', 'Timestamp (auto)'),
            ('lot', 'Lot number'),
            ('eq_indicator', 'Digital force indicator (EQ0155-01)'),
            ('eq_stand', 'Force test stand (EQ0155-03)'),
            ('load_cell', 'Load cell (EQ0155-05-A/B)'),
            ('comments', 'Comments'),
        ]

        for key, label in fields:
            row = ttk.Frame(frm)
            row.pack(fill='x', padx=6, pady=4)
            ttk.Label(row, text=label+':', width=28).pack(side='left')
            ent = ttk.Entry(row)
            ent.pack(side='left', fill='x', expand=True)
            self.entries[key] = ent
            if key != 'timestamp':
                btn = ttk.Button(row, text='Capture', width=8, command=lambda k=key: self.start_capture(k))
                btn.pack(side='left', padx=4)

        # set timestamp automatically
        self.entries['timestamp'].insert(0, utc_now_iso())

        btns = ttk.Frame(frm)
        btns.pack(fill='x', pady=10, padx=6)
        ttk.Button(btns, text='Save Form', command=self.save_form).pack(side='left')
        ttk.Button(btns, text='Clear', command=self.clear_form).pack(side='left', padx=8)
        ttk.Button(btns, text='Export CSV', command=self.export_csv).pack(side='left')

        # hidden capture entry to receive scanner keyboard input
        self.capture_entry = ttk.Entry(self)
        self.capture_entry.place_forget()
        self.capture_entry.bind('<Key>', self.on_key)
        self.capture_entry.bind('<Return>', self.on_return)

    def start_capture(self, key):
        self.current_capture_target = key
        self.capture_buffer = ''
        self.capture_entry.delete(0, 'end')
        self.capture_entry.place(x=0, y=0)  # make it focusable
        self.capture_entry.focus_set()
        messagebox.showinfo('Capture', f'Now scan or type value for {key}. Scanner input will be captured.')

    def on_key(self, event):
        ch = event.char
        if ch:
            self.capture_buffer += ch
        # schedule flush after idle
        if self.capture_timer:
            self.after_cancel(self.capture_timer)
        self.capture_timer = self.after(self.flush_delay, self.flush_capture)

    def on_return(self, event=None):
        # explicit enter
        self.flush_capture()

    def flush_capture(self):
        if not self.current_capture_target:
            return
        val = self.capture_buffer.strip()
        if val:
            self.entries[self.current_capture_target].delete(0, 'end')
            self.entries[self.current_capture_target].insert(0, val)
        # reset
        self.capture_buffer = ''
        self.current_capture_target = None
        self.capture_entry.place_forget()
        self.capture_timer = None

    def save_form(self):
        rec = {k: self.entries[k].get().strip() for k in self.entries}
        rec['saved_at'] = utc_now_iso()
        # append
        with open('fm6_filled.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec) + '\n')
        messagebox.showinfo('Saved', 'Form saved to fm6_filled.jsonl')

    def clear_form(self):
        for k, e in self.entries.items():
            e.delete(0, 'end')
        self.entries['timestamp'].insert(0, utc_now_iso())

    def export_csv(self):
        # simple export of fm6_filled.jsonl to csv
        try:
            import csv
            if not os.path.exists('fm6_filled.jsonl'):
                messagebox.showinfo('Export', 'No filled forms to export')
                return
            rows = []
            with open('fm6_filled.jsonl', 'r', encoding='utf-8') as f:
                for line in f:
                    rows.append(json.loads(line))
            keys = list(self.entries.keys()) + ['saved_at']
            with open('fm6_filled.csv', 'w', newline='', encoding='utf-8') as outf:
                w = csv.writer(outf)
                w.writerow(keys)
                for r in rows:
                    w.writerow([r.get(k, '') for k in keys])
            messagebox.showinfo('Export', 'Wrote fm6_filled.csv')
        except Exception as e:
            messagebox.showerror('Export error', str(e))


def main():
    app = FM6App()
    app.mainloop()


if __name__ == '__main__':
    main()
