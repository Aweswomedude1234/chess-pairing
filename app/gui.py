"""
gui.py — ChessPair desktop GUI built with tkinter + ttk.
Dark chess-board themed interface. All tabs: Setup, Sections, Players,
Pairings, Results, Standings.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import csv
import io
import os

from app.models import (
    Tournament, Section, Player, Round, Pairing,
    generate_round1, generate_swiss_round,
    get_standings, auto_assign_section,
    save_tournament, load_tournament, compute_tiebreaks,
)

# ─── Theme ────────────────────────────────────────────────────────────────────
BG       = "#312e2b"
SURFACE  = "#3d3a36"
SURFACE2 = "#4a4743"
BORDER   = "#524f4b"
ACCENT   = "#b58863"
ACCENT_L = "#c9a97a"
TEXT     = "#f0ede8"
MUTED    = "#b0ada8"
DIM      = "#7a7875"
SUCCESS  = "#6aaa64"
DANGER   = "#c0392b"
WARNING  = "#e8a838"
INFO     = "#4a9eca"
WHITE_C  = "#e8e0d8"
BLACK_C  = "#2a2724"

FONT_BODY   = ("Segoe UI", 10)
FONT_BOLD   = ("Segoe UI", 10, "bold")
FONT_TITLE  = ("Georgia", 14, "bold")
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Courier New", 9)

RESULT_LABELS = {"1-0": "White wins", "0-1": "Black wins", "1/2-1/2": "Draw"}


def style_btn(btn: tk.Button, variant="default"):
    colors = {
        "primary": (ACCENT, BG),
        "danger":  (DANGER, TEXT),
        "success": (SUCCESS, BG),
        "ghost":   (SURFACE2, TEXT),
        "default": (SURFACE, TEXT),
    }
    bg, fg = colors.get(variant, colors["default"])
    btn.configure(
        background=bg, foreground=fg, activebackground=ACCENT_L,
        activeforeground=BG, relief="flat", cursor="hand2",
        font=FONT_BOLD, padx=10, pady=5,
    )


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 24
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, background="#1e1c18", foreground=TEXT,
                 font=FONT_SMALL, padx=8, pady=4).pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ─── Main Application Window ─────────────────────────────────────────────────

class TournamentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChessPair — USCF Swiss Tournament Manager")
        self.geometry("1200x780")
        self.minsize(900, 620)
        self.configure(bg=BG)

        # State
        self.tournament = Tournament()
        self.sections: list[Section] = [
            Section(name="Open"), Section(name="U1800", max_rating=1799),
            Section(name="U1600", max_rating=1599), Section(name="U1400", max_rating=1399),
        ]
        self.players: list[Player] = []
        self.rounds: list[Round] = []
        self.current_file: str | None = None

        self._build_menu()
        self._build_header()
        self._build_tabs()
        self._refresh_all()

    # ── Menu ──────────────────────────────────────────────────────────────────
    def _build_menu(self):
        mb = tk.Menu(self, bg=SURFACE, fg=TEXT, activebackground=ACCENT, activeforeground=BG)
        self.configure(menu=mb)

        fm = tk.Menu(mb, tearoff=0, bg=SURFACE, fg=TEXT, activebackground=ACCENT, activeforeground=BG)
        mb.add_cascade(label="File", menu=fm)
        fm.add_command(label="New Tournament",  command=self._new_tournament)
        fm.add_command(label="Open…",           command=self._open_file)
        fm.add_command(label="Save",            command=self._save_file)
        fm.add_command(label="Save As…",        command=self._save_file_as)
        fm.add_separator()
        fm.add_command(label="Export Standings CSV…", command=self._export_standings_csv)
        fm.add_command(label="Export Pairings CSV…",  command=self._export_pairings_csv)
        fm.add_separator()
        fm.add_command(label="Exit", command=self.quit)

        hm = tk.Menu(mb, tearoff=0, bg=SURFACE, fg=TEXT, activebackground=ACCENT, activeforeground=BG)
        mb.add_cascade(label="Help", menu=hm)
        hm.add_command(label="About ChessPair", command=self._about)

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=SURFACE, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="♟", bg=SURFACE, fg=ACCENT, font=("Georgia", 22)).pack(side="left", padx=(14, 4), pady=4)
        self._title_var = tk.StringVar(value="ChessPair")
        tk.Label(hdr, textvariable=self._title_var, bg=SURFACE, fg=TEXT, font=FONT_TITLE).pack(side="left", pady=4)

        self._status_var = tk.StringVar(value="Setup mode")
        tk.Label(hdr, textvariable=self._status_var, bg=SURFACE, fg=MUTED, font=FONT_SMALL).pack(side="right", padx=16)
        self._round_var = tk.StringVar(value="Round: —")
        tk.Label(hdr, textvariable=self._round_var, bg=SURFACE, fg=ACCENT, font=FONT_BOLD).pack(side="right", padx=8)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    def _build_tabs(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
        style.configure("TNotebook.Tab", background=SURFACE, foreground=MUTED,
                        padding=[16, 8], font=FONT_BOLD, borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT), ("active", SURFACE2)],
                  foreground=[("selected", BG), ("active", TEXT)])

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=0, pady=0)

        self.tab_setup     = tk.Frame(self.nb, bg=BG)
        self.tab_sections  = tk.Frame(self.nb, bg=BG)
        self.tab_players   = tk.Frame(self.nb, bg=BG)
        self.tab_pairings  = tk.Frame(self.nb, bg=BG)
        self.tab_results   = tk.Frame(self.nb, bg=BG)
        self.tab_standings = tk.Frame(self.nb, bg=BG)

        self.nb.add(self.tab_setup,     text="  Setup  ")
        self.nb.add(self.tab_sections,  text="  Sections  ")
        self.nb.add(self.tab_players,   text="  Players  ")
        self.nb.add(self.tab_pairings,  text="  Pairings  ")
        self.nb.add(self.tab_results,   text="  Results  ")
        self.nb.add(self.tab_standings, text="  Standings  ")

        self._build_setup_tab()
        self._build_sections_tab()
        self._build_players_tab()
        self._build_pairings_tab()
        self._build_results_tab()
        self._build_standings_tab()

    # ─────────────────────────────────────────────────────────────────────────
    #  SETUP TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _build_setup_tab(self):
        pad = tk.Frame(self.tab_setup, bg=BG)
        pad.pack(fill="both", expand=True, padx=32, pady=24)

        tk.Label(pad, text="Tournament Information", bg=BG, fg=ACCENT, font=FONT_TITLE).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        fields = [
            ("Tournament Name",  "name"),
            ("Location",         "location"),
            ("Date (YYYY-MM-DD)","date"),
            ("Time Control",     "time_control"),
            ("Number of Rounds", "num_rounds"),
        ]
        self._setup_vars = {}
        for i, (label, key) in enumerate(fields, start=1):
            tk.Label(pad, text=label, bg=BG, fg=MUTED, font=FONT_BODY, anchor="w", width=22).grid(
                row=i, column=0, sticky="w", pady=5)
            var = tk.StringVar(value=str(getattr(self.tournament, key)))
            entry = tk.Entry(pad, textvariable=var, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                             relief="flat", font=FONT_BODY, width=36)
            entry.grid(row=i, column=1, sticky="w", padx=(8, 0), pady=5, ipady=5)
            self._setup_vars[key] = var

        btn = tk.Button(pad, text="Save Settings", command=self._save_setup)
        style_btn(btn, "primary")
        btn.grid(row=len(fields) + 1, column=1, sticky="w", pady=(16, 0), padx=(8, 0))

    def _save_setup(self):
        self.tournament.name         = self._setup_vars["name"].get().strip() or "Tournament"
        self.tournament.location     = self._setup_vars["location"].get().strip()
        self.tournament.date         = self._setup_vars["date"].get().strip()
        self.tournament.time_control = self._setup_vars["time_control"].get().strip()
        try:
            self.tournament.num_rounds = int(self._setup_vars["num_rounds"].get())
        except ValueError:
            pass
        self._refresh_header()
        messagebox.showinfo("Saved", "Tournament settings saved.")

    # ─────────────────────────────────────────────────────────────────────────
    #  SECTIONS TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _build_sections_tab(self):
        f = self.tab_sections
        top = tk.Frame(f, bg=BG)
        top.pack(fill="x", padx=20, pady=16)

        tk.Label(top, text="Sections", bg=BG, fg=ACCENT, font=FONT_TITLE).pack(side="left")
        add_btn = tk.Button(top, text="+ Add Section", command=self._add_section_dialog)
        style_btn(add_btn, "primary")
        add_btn.pack(side="right")

        cols = ("Name", "Max Rating", "Min Rating", "Players")
        self.sec_tree = ttk.Treeview(f, columns=cols, show="headings", height=16)
        self._style_tree(self.sec_tree)
        for c in cols:
            self.sec_tree.heading(c, text=c)
            self.sec_tree.column(c, width=160, anchor="center")
        self.sec_tree.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        btns = tk.Frame(f, bg=BG)
        btns.pack(padx=20, pady=4, anchor="w")
        rb = tk.Button(btns, text="Remove Section", command=self._remove_section)
        style_btn(rb, "danger")
        rb.pack(side="left", padx=(0, 8))

    def _add_section_dialog(self):
        win = tk.Toplevel(self)
        win.title("Add Section")
        win.configure(bg=BG)
        win.resizable(False, False)

        fields = [("Section Name", "name", "Open"), ("Max Rating (blank=none)", "max", ""),
                  ("Min Rating (blank=none)", "min", "")]
        vars_ = {}
        for i, (lbl, key, default) in enumerate(fields):
            tk.Label(win, text=lbl, bg=BG, fg=MUTED, font=FONT_BODY).grid(row=i, column=0, sticky="w", padx=16, pady=6)
            v = tk.StringVar(value=default)
            tk.Entry(win, textvariable=v, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                     font=FONT_BODY, width=22, relief="flat").grid(row=i, column=1, padx=16, pady=6, ipady=4)
            vars_[key] = v

        def confirm():
            name = vars_["name"].get().strip()
            if not name:
                messagebox.showwarning("Error", "Name required.", parent=win)
                return
            max_r = int(vars_["max"].get()) if vars_["max"].get().strip() else None
            min_r = int(vars_["min"].get()) if vars_["min"].get().strip() else None
            self.sections.append(Section(name=name, max_rating=max_r, min_rating=min_r))
            self._refresh_sections()
            win.destroy()

        ok = tk.Button(win, text="Add Section", command=confirm)
        style_btn(ok, "primary")
        ok.grid(row=len(fields), column=1, sticky="e", padx=16, pady=12)

    def _remove_section(self):
        sel = self.sec_tree.selection()
        if not sel:
            return
        sec_name = self.sec_tree.item(sel[0])["values"][0]
        sec = next((s for s in self.sections if s.name == sec_name), None)
        if sec and any(p.section_id == sec.id for p in self.players):
            messagebox.showerror("Error", "Cannot remove a section that has players assigned.")
            return
        if sec:
            self.sections = [s for s in self.sections if s.id != sec.id]
            self._refresh_sections()

    # ─────────────────────────────────────────────────────────────────────────
    #  PLAYERS TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _build_players_tab(self):
        f = self.tab_players
        top = tk.Frame(f, bg=BG)
        top.pack(fill="x", padx=20, pady=12)
        tk.Label(top, text="Players", bg=BG, fg=ACCENT, font=FONT_TITLE).pack(side="left")

        for lbl, cmd in [("+ Add Player", self._add_player_dialog),
                          ("Bulk Import (CSV)", self._bulk_import),
                          ("Export CSV", self._export_players_csv)]:
            b = tk.Button(top, text=lbl, command=cmd)
            style_btn(b, "primary" if "Add" in lbl else "default")
            b.pack(side="right", padx=4)

        # Filter bar
        fbar = tk.Frame(f, bg=BG)
        fbar.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(fbar, text="Section:", bg=BG, fg=MUTED, font=FONT_SMALL).pack(side="left")
        self._player_filter_var = tk.StringVar(value="All")
        self._player_filter_cb = ttk.Combobox(fbar, textvariable=self._player_filter_var,
                                               state="readonly", width=14, font=FONT_SMALL)
        self._player_filter_cb.pack(side="left", padx=6)
        self._player_filter_cb.bind("<<ComboboxSelected>>", lambda _: self._refresh_players())

        cols = ("#", "Name", "USCF ID", "Rating", "Section", "Score", "Status")
        self.pl_tree = ttk.Treeview(f, columns=cols, show="headings", height=22)
        self._style_tree(self.pl_tree)
        widths = [40, 200, 100, 80, 120, 70, 90]
        for c, w in zip(cols, widths):
            self.pl_tree.heading(c, text=c)
            self.pl_tree.column(c, width=w, anchor="center" if c in ("#","Rating","Score") else "w")
        scroll = ttk.Scrollbar(f, orient="vertical", command=self.pl_tree.yview)
        self.pl_tree.configure(yscrollcommand=scroll.set)
        self.pl_tree.pack(side="left", fill="both", expand=True, padx=(20, 0))
        scroll.pack(side="left", fill="y", pady=2)

        btns = tk.Frame(f, bg=BG)
        btns.pack(side="left", fill="y", padx=12, pady=0, anchor="n")
        for lbl, cmd, v in [("Edit", self._edit_player, "default"),
                              ("Withdraw / Reinstate", self._toggle_withdraw, "ghost"),
                              ("Remove", self._remove_player, "danger")]:
            b = tk.Button(btns, text=lbl, command=cmd, width=18)
            style_btn(b, v)
            b.pack(pady=4, anchor="w")

    def _add_player_dialog(self, player: Player | None = None):
        win = tk.Toplevel(self)
        win.title("Edit Player" if player else "Add Player")
        win.configure(bg=BG)
        win.resizable(False, False)

        fields = [("Name *", "name", player.name if player else ""),
                  ("USCF ID", "uscf_id", player.uscf_id if player else ""),
                  ("Rating *", "rating", str(player.rating) if player else "1200")]
        vars_ = {}
        for i, (lbl, key, default) in enumerate(fields):
            tk.Label(win, text=lbl, bg=BG, fg=MUTED, font=FONT_BODY).grid(row=i, column=0, sticky="w", padx=16, pady=6)
            v = tk.StringVar(value=default)
            tk.Entry(win, textvariable=v, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                     font=FONT_BODY, width=28, relief="flat").grid(row=i, column=1, padx=16, pady=6, ipady=4)
            vars_[key] = v

        # Section selector
        tk.Label(win, text="Section", bg=BG, fg=MUTED, font=FONT_BODY).grid(row=len(fields), column=0, sticky="w", padx=16, pady=6)
        sec_var = tk.StringVar()
        sec_cb = ttk.Combobox(win, textvariable=sec_var, state="readonly", width=26, font=FONT_BODY)
        sec_cb["values"] = ["Auto"] + [s.name for s in self.sections]
        sec_cb.current(0)
        sec_cb.grid(row=len(fields), column=1, padx=16, pady=6)
        if player:
            cur_sec = next((s.name for s in self.sections if s.id == player.section_id), "Auto")
            sec_var.set(cur_sec)

        def on_rating_change(*_):
            if sec_var.get() == "Auto":
                try:
                    r = int(vars_["rating"].get())
                    sid = auto_assign_section(r, self.sections)
                    sec = next((s for s in self.sections if s.id == sid), None)
                    if sec:
                        sec_var.set("Auto → " + sec.name)
                except ValueError:
                    pass
        vars_["rating"].trace_add("write", on_rating_change)
        on_rating_change()

        def confirm():
            name = vars_["name"].get().strip()
            if not name:
                messagebox.showwarning("Error", "Name is required.", parent=win)
                return
            try:
                rating = int(vars_["rating"].get())
            except ValueError:
                messagebox.showwarning("Error", "Rating must be a number.", parent=win)
                return

            chosen = sec_var.get()
            if chosen.startswith("Auto"):
                sid = auto_assign_section(rating, self.sections)
            else:
                sid = next((s.id for s in self.sections if s.name == chosen), None)
                if sid is None:
                    sid = auto_assign_section(rating, self.sections)

            if player:
                player.name = name
                player.uscf_id = vars_["uscf_id"].get().strip()
                player.rating = rating
                player.section_id = sid
            else:
                self.players.append(Player(
                    name=name, uscf_id=vars_["uscf_id"].get().strip(),
                    rating=rating, section_id=sid,
                ))
            self._refresh_players()
            win.destroy()

        ok = tk.Button(win, text="Save", command=confirm)
        style_btn(ok, "primary")
        ok.grid(row=len(fields) + 1, column=1, sticky="e", padx=16, pady=12)

    def _edit_player(self):
        sel = self.pl_tree.selection()
        if not sel:
            return
        pid = self.pl_tree.item(sel[0])["tags"][0]
        player = next((p for p in self.players if p.id == pid), None)
        if player:
            self._add_player_dialog(player)

    def _remove_player(self):
        sel = self.pl_tree.selection()
        if not sel:
            return
        pid = self.pl_tree.item(sel[0])["tags"][0]
        if messagebox.askyesno("Remove", "Remove this player?"):
            self.players = [p for p in self.players if p.id != pid]
            self._refresh_players()

    def _toggle_withdraw(self):
        sel = self.pl_tree.selection()
        if not sel:
            return
        pid = self.pl_tree.item(sel[0])["tags"][0]
        player = next((p for p in self.players if p.id == pid), None)
        if player:
            player.withdrawn = not player.withdrawn
            self._refresh_players()

    def _bulk_import(self):
        """Import players from a CSV/text file: Name,Rating,USCF_ID per line."""
        fp = filedialog.askopenfilename(title="Import Players",
                                        filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All", "*.*")])
        if not fp:
            return
        added = 0
        with open(fp, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].strip().lower() in ("name", "#"):
                    continue
                name = row[0].strip()
                rating = int(row[1].strip()) if len(row) > 1 and row[1].strip().isdigit() else 1200
                uscf_id = row[2].strip() if len(row) > 2 else ""
                sid = auto_assign_section(rating, self.sections)
                self.players.append(Player(name=name, rating=rating, uscf_id=uscf_id, section_id=sid))
                added += 1
        self._refresh_players()
        messagebox.showinfo("Import", f"{added} players imported.")

    def _export_players_csv(self):
        fp = filedialog.asksaveasfilename(defaultextension=".csv",
                                          filetypes=[("CSV", "*.csv")])
        if not fp:
            return
        sec_name = {s.id: s.name for s in self.sections}
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Name", "USCF ID", "Rating", "Section", "Score"])
            for p in self.players:
                w.writerow([p.name, p.uscf_id, p.rating, sec_name.get(p.section_id, ""), p.score])
        messagebox.showinfo("Export", f"Exported to {fp}")

    # ─────────────────────────────────────────────────────────────────────────
    #  PAIRINGS TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _build_pairings_tab(self):
        f = self.tab_pairings
        top = tk.Frame(f, bg=BG)
        top.pack(fill="x", padx=20, pady=12)

        tk.Label(top, text="Pairings", bg=BG, fg=ACCENT, font=FONT_TITLE).pack(side="left")
        self._pair_round_var = tk.StringVar(value="Round —")
        tk.Label(top, textvariable=self._pair_round_var, bg=BG, fg=MUTED, font=FONT_BOLD).pack(side="left", padx=16)

        gen_btn = tk.Button(top, text="⚡ Generate Next Round", command=self._generate_round)
        style_btn(gen_btn, "primary")
        gen_btn.pack(side="right", padx=4)
        exp_btn = tk.Button(top, text="Export Pairing Sheet", command=self._export_pairings_csv)
        style_btn(exp_btn)
        exp_btn.pack(side="right", padx=4)

        # Section selector
        sbar = tk.Frame(f, bg=BG)
        sbar.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(sbar, text="Section:", bg=BG, fg=MUTED, font=FONT_SMALL).pack(side="left")
        self._pair_sec_var = tk.StringVar()
        self._pair_sec_cb = ttk.Combobox(sbar, textvariable=self._pair_sec_var, state="readonly", width=16)
        self._pair_sec_cb.pack(side="left", padx=6)
        self._pair_sec_cb.bind("<<ComboboxSelected>>", lambda _: self._refresh_pairings_view())

        # Bye info
        self._bye_var = tk.StringVar(value="")
        tk.Label(sbar, textvariable=self._bye_var, bg=BG, fg=WARNING, font=FONT_BOLD).pack(side="right", padx=8)

        cols = ("Bd", "White", "Rating", "vs", "Black", "Rating ", "Result")
        self.pair_tree = ttk.Treeview(f, columns=cols, show="headings", height=24)
        self._style_tree(self.pair_tree)
        widths = [40, 200, 80, 30, 200, 80, 100]
        anchors = ["center","w","center","center","w","center","center"]
        for c, w, a in zip(cols, widths, anchors):
            self.pair_tree.heading(c, text=c)
            self.pair_tree.column(c, width=w, anchor=a)
        scroll = ttk.Scrollbar(f, orient="vertical", command=self.pair_tree.yview)
        self.pair_tree.configure(yscrollcommand=scroll.set)
        self.pair_tree.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 12))
        scroll.pack(side="left", fill="y", pady=2)

    def _generate_round(self):
        active = [p for p in self.players if not p.withdrawn]
        if len(active) < 2:
            messagebox.showwarning("Error", "Need at least 2 active players.")
            return
        if self.tournament.current_round >= self.tournament.num_rounds:
            messagebox.showinfo("Done", "All rounds complete.")
            return

        round_num = self.tournament.current_round + 1
        new_round = Round(number=round_num)

        for sec in self.sections:
            sp = [p for p in active if p.section_id == sec.id]
            if len(sp) < 2:
                continue
            if round_num == 1:
                pairs, bye_id = generate_round1(sp)
            else:
                pairs, bye_id = generate_swiss_round(sp)

            new_round.pairings.extend(pairs)
            if bye_id:
                new_round.byes[sec.id] = bye_id

        if not new_round.pairings:
            messagebox.showwarning("Error", "Could not generate pairings.")
            return

        self.rounds.append(new_round)
        self.tournament.current_round = round_num
        self.tournament.status = "active"
        self._refresh_all()
        messagebox.showinfo("Pairings", f"Round {round_num} pairings generated. Enter results in the Results tab.")
        self.nb.select(self.tab_pairings)

    # ─────────────────────────────────────────────────────────────────────────
    #  RESULTS TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _build_results_tab(self):
        f = self.tab_results
        top = tk.Frame(f, bg=BG)
        top.pack(fill="x", padx=20, pady=12)
        tk.Label(top, text="Enter Results", bg=BG, fg=ACCENT, font=FONT_TITLE).pack(side="left")

        sbar = tk.Frame(f, bg=BG)
        sbar.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(sbar, text="Section:", bg=BG, fg=MUTED, font=FONT_SMALL).pack(side="left")
        self._res_sec_var = tk.StringVar()
        self._res_sec_cb = ttk.Combobox(sbar, textvariable=self._res_sec_var, state="readonly", width=16)
        self._res_sec_cb.pack(side="left", padx=6)
        self._res_sec_cb.bind("<<ComboboxSelected>>", lambda _: self._refresh_results_view())

        self._res_bye_var = tk.StringVar()
        tk.Label(sbar, textvariable=self._res_bye_var, bg=BG, fg=WARNING, font=FONT_BOLD).pack(side="right", padx=8)

        # Scrollable frame for result entry
        canvas = tk.Canvas(f, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        self.res_scroll_frame = tk.Frame(canvas, bg=BG)
        self.res_scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.res_scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))
        scrollbar.pack(side="left", fill="y")

    def _refresh_results_view(self):
        for w in self.res_scroll_frame.winfo_children():
            w.destroy()
        if not self.rounds:
            tk.Label(self.res_scroll_frame, text="Generate pairings first.", bg=BG, fg=MUTED, font=FONT_BODY).pack(pady=24)
            return

        r = self.rounds[-1]
        by_id = {p.id: p for p in self.players}
        sec_id = next((s.id for s in self.sections if s.name == self._res_sec_var.get()), None)

        # BYE display
        bye_id = r.byes.get(sec_id) if sec_id else None
        if bye_id and by_id.get(bye_id):
            self._res_bye_var.set(f"BYE (+1): {by_id[bye_id].name}")
        else:
            self._res_bye_var.set("")

        pairs = [p for p in r.pairings
                 if by_id.get(p.white_id, Player()).section_id == sec_id
                 or by_id.get(p.black_id, Player()).section_id == sec_id] if sec_id else r.pairings

        if not pairs:
            tk.Label(self.res_scroll_frame, text="No pairings for this section.", bg=BG, fg=MUTED, font=FONT_BODY).pack(pady=24)
            return

        # Column headers
        hdr = tk.Frame(self.res_scroll_frame, bg=SURFACE)
        hdr.pack(fill="x", pady=(0, 2))
        for txt, w in [("Bd", 40), ("White", 200), ("  vs  ", 50), ("Black", 200), ("Result", 260)]:
            tk.Label(hdr, text=txt, bg=SURFACE, fg=MUTED, font=FONT_SMALL, width=w//8, anchor="center").pack(side="left", padx=4, pady=4)

        for i, pair in enumerate(pairs):
            white = by_id.get(pair.white_id, Player(name="?"))
            black = by_id.get(pair.black_id, Player(name="?"))
            row = tk.Frame(self.res_scroll_frame, bg=SURFACE if i % 2 == 0 else BG)
            row.pack(fill="x", pady=1)

            tk.Label(row, text=str(i + 1), bg=row["bg"], fg=DIM, font=FONT_MONO, width=4).pack(side="left", padx=6, pady=6)
            tk.Label(row, text=f"{white.name} ({white.rating})", bg=row["bg"], fg=TEXT, font=FONT_BODY, width=26, anchor="w").pack(side="left")
            tk.Label(row, text="vs", bg=row["bg"], fg=DIM, font=FONT_SMALL, width=4).pack(side="left")
            tk.Label(row, text=f"{black.name} ({black.rating})", bg=row["bg"], fg=TEXT, font=FONT_BODY, width=26, anchor="w").pack(side="left")

            for result_val, btn_label, color in [("1-0", "1–0", SUCCESS), ("1/2-1/2", "½–½", WARNING), ("0-1", "0–1", DANGER)]:
                is_set = pair.result == result_val
                b = tk.Button(row, text=btn_label,
                              bg=color if is_set else SURFACE2,
                              fg=BG if is_set else TEXT,
                              relief="flat", font=FONT_BOLD, padx=12, pady=4, cursor="hand2",
                              command=lambda p=pair, rv=result_val: self._set_result(p, rv))
                b.pack(side="left", padx=3, pady=4)

    def _set_result(self, pair: Pairing, result: str):
        if pair.result == result:
            return  # no change

        by_id = {p.id: p for p in self.players}

        # Undo previous result if any
        if pair.result is not None:
            self._undo_result(pair, by_id)

        pair.result = result
        white = by_id.get(pair.white_id)
        black = by_id.get(pair.black_id)
        if not white or not black:
            return

        if result == "1-0":
            w_res, b_res, w_pts, b_pts = "W", "L", 1.0, 0.0
        elif result == "0-1":
            w_res, b_res, w_pts, b_pts = "L", "W", 0.0, 1.0
        else:
            w_res, b_res, w_pts, b_pts = "D", "D", 0.5, 0.5

        white.score += w_pts
        white.opponents.append(black.id)
        white.colors.append("W")
        white.results.append(w_res)
        white.cumulative_scores.append(white.score)

        black.score += b_pts
        black.opponents.append(white.id)
        black.colors.append("B")
        black.results.append(b_res)
        black.cumulative_scores.append(black.score)

        # Handle bye for this round / section
        r = self.rounds[-1]
        for sec in self.sections:
            bye_id = r.byes.get(sec.id)
            if bye_id:
                bye_player = by_id.get(bye_id)
                if bye_player and not bye_player.has_received_bye:
                    bye_player.score += 1.0
                    bye_player.has_received_bye = True
                    bye_player.cumulative_scores.append(bye_player.score)

        self._refresh_results_view()
        self._refresh_standings()

    def _undo_result(self, pair: Pairing, by_id: dict):
        """Reverse score/opponent/color changes for a previously entered result."""
        white = by_id.get(pair.white_id)
        black = by_id.get(pair.black_id)
        if not white or not black:
            return

        res = pair.result
        if res == "1-0":
            w_pts, b_pts = 1.0, 0.0
        elif res == "0-1":
            w_pts, b_pts = 0.0, 1.0
        else:
            w_pts, b_pts = 0.5, 0.5

        # Remove last entry if it matches this game
        if white.opponents and white.opponents[-1] == black.id:
            white.score -= w_pts
            white.opponents.pop()
            white.colors.pop()
            white.results.pop()
            if white.cumulative_scores:
                white.cumulative_scores.pop()

        if black.opponents and black.opponents[-1] == white.id:
            black.score -= b_pts
            black.opponents.pop()
            black.colors.pop()
            black.results.pop()
            if black.cumulative_scores:
                black.cumulative_scores.pop()

    # ─────────────────────────────────────────────────────────────────────────
    #  STANDINGS TAB
    # ─────────────────────────────────────────────────────────────────────────
    def _build_standings_tab(self):
        f = self.tab_standings
        top = tk.Frame(f, bg=BG)
        top.pack(fill="x", padx=20, pady=12)
        tk.Label(top, text="Standings", bg=BG, fg=ACCENT, font=FONT_TITLE).pack(side="left")

        sbar = tk.Frame(f, bg=BG)
        sbar.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(sbar, text="Section:", bg=BG, fg=MUTED, font=FONT_SMALL).pack(side="left")
        self._stand_sec_var = tk.StringVar()
        self._stand_sec_cb = ttk.Combobox(sbar, textvariable=self._stand_sec_var, state="readonly", width=16)
        self._stand_sec_cb.pack(side="left", padx=6)
        self._stand_sec_cb.bind("<<ComboboxSelected>>", lambda _: self._refresh_standings())

        exp = tk.Button(sbar, text="Export Standings CSV", command=self._export_standings_csv)
        style_btn(exp)
        exp.pack(side="right")

        cols = ("Place", "Name", "Rating", "Score", "Results", "Mod.Med", "Solkoff", "Cumul.", "Opp.Cum.", "S-B")
        self.stand_tree = ttk.Treeview(f, columns=cols, show="headings", height=26)
        self._style_tree(self.stand_tree)
        widths = [55, 200, 70, 65, 130, 75, 75, 75, 80, 65]
        for c, w in zip(cols, widths):
            self.stand_tree.heading(c, text=c)
            self.stand_tree.column(c, width=w, anchor="center" if c not in ("Name",) else "w")
        scroll = ttk.Scrollbar(f, orient="vertical", command=self.stand_tree.yview)
        self.stand_tree.configure(yscrollcommand=scroll.set)
        self.stand_tree.pack(side="left", fill="both", expand=True, padx=(20, 0))
        scroll.pack(side="left", fill="y")

    # ─────────────────────────────────────────────────────────────────────────
    #  REFRESH HELPERS
    # ─────────────────────────────────────────────────────────────────────────
    def _style_tree(self, tree: ttk.Treeview):
        style = ttk.Style()
        sn = f"Custom{id(tree)}.Treeview"
        style.configure(sn, background=SURFACE, foreground=TEXT, rowheight=26,
                        fieldbackground=SURFACE, borderwidth=0, font=FONT_BODY)
        style.configure(f"{sn}.Heading", background=BG, foreground=MUTED,
                        font=FONT_SMALL, relief="flat", borderwidth=0)
        style.map(sn, background=[("selected", ACCENT)], foreground=[("selected", BG)])
        tree.configure(style=sn)
        tree.tag_configure("alt", background=SURFACE2)
        tree.tag_configure("withdrawn", foreground=DANGER)

    def _refresh_all(self):
        self._refresh_header()
        self._refresh_sections()
        self._refresh_players()
        self._refresh_pairings_view()
        self._refresh_results_view()
        self._refresh_standings()

    def _refresh_header(self):
        self._title_var.set(f"♟ {self.tournament.name}")
        self._status_var.set(f"Status: {self.tournament.status.title()}")
        self._round_var.set(f"Round: {self.tournament.current_round}/{self.tournament.num_rounds}")

    def _refresh_sections(self):
        for row in self.sec_tree.get_children():
            self.sec_tree.delete(row)
        sec_player_counts = {s.id: sum(1 for p in self.players if p.section_id == s.id) for s in self.sections}
        for i, s in enumerate(self.sections):
            tag = "alt" if i % 2 else ""
            self.sec_tree.insert("", "end", values=(
                s.name,
                s.max_rating if s.max_rating is not None else "Open",
                s.min_rating if s.min_rating is not None else "—",
                sec_player_counts.get(s.id, 0),
            ), tags=(tag,))
        # Update section selectors
        sec_names = [s.name for s in self.sections]
        for cb in [getattr(self, "_pair_sec_cb", None), getattr(self, "_res_sec_cb", None),
                   getattr(self, "_stand_sec_cb", None), getattr(self, "_player_filter_cb", None)]:
            if cb is None:
                continue
            is_filter = cb is getattr(self, "_player_filter_cb", None)
            vals = (["All"] + sec_names) if is_filter else sec_names
            cb["values"] = vals
            if not cb.get() or cb.get() not in vals:
                cb.current(0)

    def _refresh_players(self):
        for row in self.pl_tree.get_children():
            self.pl_tree.delete(row)
        sec_name = {s.id: s.name for s in self.sections}
        filt = self._player_filter_var.get() if hasattr(self, "_player_filter_var") else "All"
        filtered = sorted(self.players, key=lambda p: -p.rating)
        if filt != "All":
            filt_id = next((s.id for s in self.sections if s.name == filt), None)
            if filt_id:
                filtered = [p for p in filtered if p.section_id == filt_id]
        for i, p in enumerate(filtered):
            tag = ("withdrawn",) if p.withdrawn else ("alt",) if i % 2 else ()
            self.pl_tree.insert("", "end", values=(
                i + 1, p.name, p.uscf_id or "—", p.rating,
                sec_name.get(p.section_id, "—"), p.score,
                "Withdrawn" if p.withdrawn else "Active",
            ), tags=(p.id, *tag))

    def _refresh_pairings_view(self):
        for row in self.pair_tree.get_children():
            self.pair_tree.delete(row)
        if not self.rounds:
            self._pair_round_var.set("Round —")
            return
        r = self.rounds[-1]
        self._pair_round_var.set(f"Round {r.number}")
        by_id = {p.id: p for p in self.players}
        sec_id = next((s.id for s in self.sections if s.name == self._pair_sec_var.get()), None)

        bye_id = r.byes.get(sec_id) if sec_id else None
        self._bye_var.set(f"BYE: {by_id[bye_id].name}" if bye_id and by_id.get(bye_id) else "")

        pairs = [p for p in r.pairings
                 if by_id.get(p.white_id, Player()).section_id == sec_id
                 or by_id.get(p.black_id, Player()).section_id == sec_id] if sec_id else r.pairings

        for i, pair in enumerate(pairs):
            white = by_id.get(pair.white_id, Player(name="?"))
            black = by_id.get(pair.black_id, Player(name="?"))
            tag = "alt" if i % 2 else ""
            self.pair_tree.insert("", "end", values=(
                i + 1, white.name, white.rating, "–",
                black.name, black.rating,
                pair.result or "Pending",
            ), tags=(tag,))

    def _refresh_standings(self):
        for row in self.stand_tree.get_children():
            self.stand_tree.delete(row)
        if not hasattr(self, "_stand_sec_var") or not self._stand_sec_var.get():
            return
        sec_id = next((s.id for s in self.sections if s.name == self._stand_sec_var.get()), None)
        if not sec_id:
            return
        standings = get_standings(self.players, sec_id)
        medals = ["🥇", "🥈", "🥉"]
        for i, p in enumerate(standings):
            place = medals[i] if i < 3 else str(i + 1)
            tb = p.tiebreaks
            results_str = " ".join(p.results) if p.results else "—"
            self.stand_tree.insert("", "end", values=(
                place, p.name, p.rating, p.score, results_str,
                f"{tb.get('mod_median', 0):.1f}",
                f"{tb.get('solkoff', 0):.1f}",
                f"{tb.get('cumulative', 0):.1f}",
                f"{tb.get('opp_cumulative', 0):.1f}",
                f"{tb.get('sonneborn_berger', 0):.1f}",
            ), tags=("alt" if i % 2 else "",))

    # ─────────────────────────────────────────────────────────────────────────
    #  FILE I/O
    # ─────────────────────────────────────────────────────────────────────────
    def _new_tournament(self):
        if messagebox.askyesno("New Tournament", "Discard current tournament and start fresh?"):
            self.tournament = Tournament()
            self.sections = [
                Section(name="Open"), Section(name="U1800", max_rating=1799),
                Section(name="U1600", max_rating=1599),
            ]
            self.players = []
            self.rounds = []
            self.current_file = None
            self._refresh_all()

    def _save_file(self):
        if self.current_file:
            save_tournament(self.current_file, self.tournament, self.sections, self.players, self.rounds)
            messagebox.showinfo("Saved", f"Saved to {self.current_file}")
        else:
            self._save_file_as()

    def _save_file_as(self):
        fp = filedialog.asksaveasfilename(defaultextension=".cpair",
                                          filetypes=[("ChessPair files", "*.cpair"), ("JSON", "*.json")])
        if fp:
            self.current_file = fp
            save_tournament(fp, self.tournament, self.sections, self.players, self.rounds)
            messagebox.showinfo("Saved", f"Saved to {fp}")

    def _open_file(self):
        fp = filedialog.askopenfilename(filetypes=[("ChessPair files", "*.cpair *.json"), ("All", "*.*")])
        if not fp:
            return
        try:
            self.tournament, self.sections, self.players, self.rounds = load_tournament(fp)
            self.current_file = fp
            self._refresh_all()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def _export_standings_csv(self):
        fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not fp:
            return
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Section","Place","Name","Rating","Score","Mod.Median","Solkoff","Cumulative","Opp.Cumul.","S-B"])
            for sec in self.sections:
                standings = get_standings(self.players, sec.id)
                for i, p in enumerate(standings):
                    tb = p.tiebreaks
                    w.writerow([sec.name, i+1, p.name, p.rating, p.score,
                                 tb.get("mod_median",0), tb.get("solkoff",0),
                                 tb.get("cumulative",0), tb.get("opp_cumulative",0),
                                 tb.get("sonneborn_berger",0)])
        messagebox.showinfo("Export", f"Exported to {fp}")

    def _export_pairings_csv(self):
        if not self.rounds:
            messagebox.showwarning("Error", "No pairings to export.")
            return
        fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not fp:
            return
        r = self.rounds[-1]
        by_id = {p.id: p for p in self.players}
        sec_name = {s.id: s.name for s in self.sections}
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Round","Board","White","White Rating","Black","Black Rating","Result","Section"])
            for i, pair in enumerate(r.pairings):
                white = by_id.get(pair.white_id, Player(name="?"))
                black = by_id.get(pair.black_id, Player(name="?"))
                w.writerow([r.number, i+1, white.name, white.rating, black.name, black.rating,
                             pair.result or "", sec_name.get(white.section_id, "")])
        messagebox.showinfo("Export", f"Pairings exported to {fp}")

    def _about(self):
        messagebox.showinfo("About ChessPair",
            "ChessPair v1.0.0\n\n"
            "Free, open-source USCF Swiss tournament pairing software.\n"
            "MIT License. Not affiliated with USCF.\n\n"
            "github.com/YOUR_USERNAME/chesspair")
