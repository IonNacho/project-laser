#!/usr/bin/env python3
"""Simple FM6 tensile test form GUI.

Screens:
- Lot Record Traceability
- Equipment (EQ0070 or EQ0155)
- Tooling / Fixtures (confirm required tools)
- Results (four tensile values, auto pass/fail)

Saves completed records to `fm6_simple.jsonl` and `fm6_simple.csv`.
Required fields must be filled before saving.
Scanner acts like keyboard; put cursor in a field and scan.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import json
import csv
import os

JSONL_FILE = 'fm6_simple.jsonl'
CSV_FILE = 'fm6_simple.csv'


def today_date():
    return datetime.date.today().isoformat()


class FM6SimpleApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('FM6 Simple Entry')
        self.geometry('800x600')

        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True)

        self.lot_frame = ttk.Frame(nb)
        self.eq_frame = ttk.Frame(nb)
        self.tools_frame = ttk.Frame(nb)
        self.results_frame = ttk.Frame(nb)

        nb.add(self.lot_frame, text='Lot Record')
        nb.add(self.eq_frame, text='Equipment')
        nb.add(self.tools_frame, text='Tooling')
        nb.add(self.results_frame, text='Results')

        self.build_lot_tab()
        self.build_equipment_tab()
        self.build_tools_tab()
        self.build_results_tab()

    def build_lot_tab(self):
        frm = self.lot_frame
        pad = {'padx': 8, 'pady': 8}

        ttk.Label(frm, text='Lot Number:').grid(row=0, column=0, sticky='w', **pad)
        self.lot_number = ttk.Entry(frm, width=40)
        self.lot_number.grid(row=0, column=1, **pad)

        ttk.Label(frm, text='Operator Signature:').grid(row=1, column=0, sticky='w', **pad)
        self.operator_sig = ttk.Entry(frm, width=40)
        self.operator_sig.grid(row=1, column=1, **pad)

        ttk.Label(frm, text='Operator Date:').grid(row=2, column=0, sticky='w', **pad)
        self.operator_date = ttk.Entry(frm, width=20)
        self.operator_date.insert(0, today_date())
        self.operator_date.grid(row=2, column=1, sticky='w', **pad)

    def build_equipment_tab(self):
        frm = self.eq_frame
        pad = {'padx': 6, 'pady': 6}

        ttk.Label(frm, text='Equipment Type:').grid(row=0, column=0, sticky='w', **pad)
        self.eq_type = tk.StringVar(value='EQ0155')
        rb1 = ttk.Radiobutton(frm, text='EQ0070', variable=self.eq_type, value='EQ0070', command=self.render_eq_rows)
        rb2 = ttk.Radiobutton(frm, text='EQ0155', variable=self.eq_type, value='EQ0155', command=self.render_eq_rows)
        rb1.grid(row=0, column=1, sticky='w', **pad)
        rb2.grid(row=0, column=2, sticky='w', **pad)

        self.eq_rows_container = ttk.Frame(frm)
        self.eq_rows_container.grid(row=1, column=0, columnspan=4, sticky='nsew')

        # define equipment sets
        self.eq_defs = {
            'EQ0070': [
                {'key': 'eq0070_unit', 'label': 'EQ0070 Unit', 'required': True},
            ],
            'EQ0155': [
                {'key': 'eq_indicator', 'label': 'Digital force indicator (EQ0155-01)', 'required': True},
                {'key': 'eq_stand', 'label': 'Force test stand (EQ0155-03)', 'required': True},
                {'key': 'load_cell', 'label': 'Load cell (EQ0155-05-A/B)', 'required': True},
            ]
        }

        # will store widgets for each equipment row
        self.eq_widgets = {}
        self.render_eq_rows()

    def render_eq_rows(self):
        for c in self.eq_rows_container.winfo_children():
            c.destroy()
        etype = self.eq_type.get()
        defs = self.eq_defs.get(etype, [])
        for i, d in enumerate(defs):
            lbl = ttk.Label(self.eq_rows_container, text=d['label'] + ':')
            lbl.grid(row=i, column=0, sticky='w', padx=6, pady=4)
            ent_id = ttk.Entry(self.eq_rows_container, width=30)
            ent_id.grid(row=i, column=1, padx=6, pady=4)
            ent_cal = ttk.Entry(self.eq_rows_container, width=15)
            ent_cal.insert(0, '')
            ent_cal.grid(row=i, column=2, padx=6, pady=4)
            ent_init = ttk.Entry(self.eq_rows_container, width=15)
            ent_init.insert(0, '')
            ent_init.grid(row=i, column=3, padx=6, pady=4)
            ttk.Label(self.eq_rows_container, text='Equipment ID').grid(row=i, column=1, sticky='s')
            ttk.Label(self.eq_rows_container, text='Cal Due Date').grid(row=i, column=2, sticky='s')
            ttk.Label(self.eq_rows_container, text='Initial Date').grid(row=i, column=3, sticky='s')
            self.eq_widgets[d['key']] = {'id': ent_id, 'cal': ent_cal, 'init': ent_init, 'required': d.get('required', False), 'label': d['label']}

    def build_tools_tab(self):
        frm = self.tools_frame
        pad = {'padx': 6, 'pady': 6}
        ttk.Label(frm, text='Confirm required tools present:').grid(row=0, column=0, sticky='w', **pad)
        tools = [
            ('T0004', 'Oblique Cutting Tweezers'),
            ('T0080', 'Carbon Steel Tweezers'),
            ('T00105', 'Tensile Tester Adapter Plate'),
            ('T00117', 'Vise Clamp'),
            ('T00173', 'Smooth Jawed Clamp'),
        ]
        self.tool_vars = {}
        for i, (k, label) in enumerate(tools, start=1):
            v = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(frm, text=f'{k} {label}', variable=v)
            cb.grid(row=i, column=0, sticky='w', padx=8, pady=4)
            self.tool_vars[k] = {'var': v, 'label': label}

    def build_results_tab(self):
        frm = self.results_frame
        pad = {'padx': 6, 'pady': 6}

        ttk.Label(frm, text='First Piece Tab A (lbf):').grid(row=0, column=0, sticky='w', **pad)
        self.first_a = ttk.Entry(frm, width=20)
        self.first_a.grid(row=0, column=1, **pad)

        ttk.Label(frm, text='First Piece Tab B (lbf):').grid(row=1, column=0, sticky='w', **pad)
        self.first_b = ttk.Entry(frm, width=20)
        self.first_b.grid(row=1, column=1, **pad)

        ttk.Label(frm, text='Last Piece Tab A (lbf):').grid(row=2, column=0, sticky='w', **pad)
        self.last_a = ttk.Entry(frm, width=20)
        self.last_a.grid(row=2, column=1, **pad)

        ttk.Label(frm, text='Last Piece Tab B (lbf):').grid(row=3, column=0, sticky='w', **pad)
        self.last_b = ttk.Entry(frm, width=20)
        self.last_b.grid(row=3, column=1, **pad)

        ttk.Label(frm, text='Data Recorded By (signature):').grid(row=4, column=0, sticky='w', **pad)
        self.data_sig = ttk.Entry(frm, width=30)
        self.data_sig.grid(row=4, column=1, **pad)

        ttk.Label(frm, text='Data Recorded Date:').grid(row=5, column=0, sticky='w', **pad)
        self.data_date = ttk.Entry(frm, width=20)
        self.data_date.insert(0, today_date())
        self.data_date.grid(row=5, column=1, **pad)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=12)
        ttk.Button(btn_frame, text='Validate and Save', command=self.validate_and_save).pack(side='left', padx=8)
        ttk.Button(btn_frame, text='Clear Form', command=self.clear_form).pack(side='left', padx=8)

    def collect_record(self):
        rec = {}
        rec['lot_number'] = self.lot_number.get().strip()
        rec['operator_signature'] = self.operator_sig.get().strip()
        rec['operator_date'] = self.operator_date.get().strip()
        rec['equipment_type'] = self.eq_type.get()
        rec['equipment'] = {}
        for k, w in self.eq_widgets.items():
            rec['equipment'][k] = {
                'id': w['id'].get().strip(),
                'cal_due': w['cal'].get().strip(),
                'initial_date': w['init'].get().strip(),
            }
        rec['tools'] = {k: v['var'].get() for k, v in self.tool_vars.items()}
        rec['results'] = {
            'first_a': self.first_a.get().strip(),
            'first_b': self.first_b.get().strip(),
            'last_a': self.last_a.get().strip(),
            'last_b': self.last_b.get().strip(),
        }
        rec['data_recorded_by'] = self.data_sig.get().strip()
        rec['data_recorded_date'] = self.data_date.get().strip()
        rec['saved_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return rec

    def validate_and_save(self):
        rec = self.collect_record()
        missing = []
        if not rec['lot_number']:
            missing.append('Lot Number')
        if not rec['operator_signature']:
            missing.append('Operator Signature')
        if not rec['operator_date']:
            missing.append('Operator Date')

        # equipment required checks
        for k, w in self.eq_widgets.items():
            if w.get('required'):
                eid = w['id'].get().strip()
                cal = w['cal'].get().strip()
                init = w['init'].get().strip()
                lbl = w.get('label', k)
                if not eid:
                    missing.append(f'{lbl} - Equipment ID')
                if not cal:
                    missing.append(f'{lbl} - Cal Due Date')
                if not init:
                    missing.append(f'{lbl} - Initial Date')

        # tools must be confirmed
        for k, v in self.tool_vars.items():
            if not v['var'].get():
                missing.append(f'Tool missing: {k} {v["label"]}')

        # results numeric checks
        vals = {}
        for name in ('first_a', 'first_b', 'last_a', 'last_b'):
            s = rec['results'][name]
            if not s:
                missing.append(f'Result missing: {name}')
            else:
                try:
                    vals[name] = float(s)
                except Exception:
                    missing.append(f'Result invalid number: {name}')

        if not rec['data_recorded_by']:
            missing.append('Data Recorded By (signature)')
        if not rec['data_recorded_date']:
            missing.append('Data Recorded Date')

        if missing:
            messagebox.showerror('Missing required fields', '\n'.join(missing))
            return

        # compute pass/fail: pass if all four values >= 5.61 lbf
        threshold = 5.61
        all_pass = all(v >= threshold for v in vals.values())
        rec['pass'] = all_pass
        rec['threshold_lbf'] = threshold

        # append to JSONL
        with open(JSONL_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec) + '\n')

        # append to CSV (create header if missing)
        fieldnames = [
            'lot_number', 'operator_signature', 'operator_date', 'equipment_type',
        ]
        # flatten equipment into columns for CSV
        for k in self.eq_widgets.keys():
            fieldnames += [f'{k}_id', f'{k}_cal_due', f'{k}_initial']
        for t in self.tool_vars.keys():
            fieldnames.append(f'tool_{t}')
        fieldnames += ['first_a', 'first_b', 'last_a', 'last_b', 'data_recorded_by', 'data_recorded_date', 'pass', 'saved_at']

        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as cf:
            w = csv.DictWriter(cf, fieldnames=fieldnames)
            if not file_exists:
                w.writeheader()
            row = {}
            row['lot_number'] = rec['lot_number']
            row['operator_signature'] = rec['operator_signature']
            row['operator_date'] = rec['operator_date']
            row['equipment_type'] = rec['equipment_type']
            for k, wdef in self.eq_widgets.items():
                row[f'{k}_id'] = wdef['id'].get().strip()
                row[f'{k}_cal_due'] = wdef['cal'].get().strip()
                row[f'{k}_initial'] = wdef['init'].get().strip()
            for t, v in self.tool_vars.items():
                row[f'tool_{t}'] = 'YES' if v['var'].get() else 'NO'
            row['first_a'] = rec['results']['first_a']
            row['first_b'] = rec['results']['first_b']
            row['last_a'] = rec['results']['last_a']
            row['last_b'] = rec['results']['last_b']
            row['data_recorded_by'] = rec['data_recorded_by']
            row['data_recorded_date'] = rec['data_recorded_date']
            row['pass'] = 'PASS' if rec['pass'] else 'FAIL'
            row['saved_at'] = rec['saved_at']
            w.writerow(row)

        messagebox.showinfo('Saved', f'Record saved. PASS={rec["pass"]}')

    def clear_form(self):
        self.lot_number.delete(0, 'end')
        self.operator_sig.delete(0, 'end')
        self.operator_date.delete(0, 'end')
        for w in self.eq_widgets.values():
            w['id'].delete(0, 'end')
            w['cal'].delete(0, 'end')
            w['init'].delete(0, 'end')
        for v in self.tool_vars.values():
            v['var'].set(False)
        self.first_a.delete(0, 'end')
        self.first_b.delete(0, 'end')
        self.last_a.delete(0, 'end')
        self.last_b.delete(0, 'end')
        self.data_sig.delete(0, 'end')
        self.data_date.delete(0, 'end')
        self.data_date.insert(0, today_date())


def main():
    app = FM6SimpleApp()
    app.mainloop()


if __name__ == '__main__':
    main()
