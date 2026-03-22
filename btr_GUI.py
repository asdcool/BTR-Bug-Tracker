#!/usr/bin/env python3
"""
BTR - Software Bug Tracker (GUI)
"""
"""
How to Run:

    Use the latest version of python to have Tkinter pre-installed
    
    python3 -m unittest -v btr_GUI.py
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

try:
    FONT_FAMILY = "Trebuchet MS"
except:
    FONT_FAMILY = "Helvetica"

BG_MAIN = "#0f172a"       # page background
BG_CARD = "#111827"       # panel background
BG_INPUT = "#1f2937"      # entry / combo / tree background
FG_MAIN = "#e5e7eb"       # main text
FG_MUTED = "#9ca3af"      # secondary text
ACCENT = "#2563eb"        # primary blue
ACCENT_HOVER = "#1d4ed8"  # darker blue
BORDER = "#374151"        # borders

DB = "btr.sqlite3"

STATUSES = ["Open", "In Progress", "Fixed", "Closed"]

TRANSITIONS = {
    "Open": {"In Progress"},
    "In Progress": {"Fixed"},
    "Fixed": {"Closed"},
    "Closed": set(),
}


def today():
    return date.today().isoformat()


def init_db(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS bugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        bug_type TEXT NOT NULL,
        artifact_type TEXT NOT NULL,
        reporter TEXT NOT NULL,
        date_found TEXT NOT NULL,
        status TEXT NOT NULL,
        date_fixed TEXT
    );
    """)
    conn.commit()

def setup_modern_style(root):
    style = ttk.Style(root)

    if "clam" in style.theme_names():
        style.theme_use("clam")

    root.configure(bg=BG_MAIN)

    style.configure(".", 
        background=BG_MAIN,
        foreground=FG_MAIN,
        fieldbackground=BG_INPUT,
        font=(FONT_FAMILY, 11)
    )

    style.configure("Title.TLabel",
        background=BG_MAIN,
        foreground=FG_MAIN,
        font=(FONT_FAMILY, 20, "bold")
    )

    style.configure("Subtitle.TLabel",
        background=BG_MAIN,
        foreground=FG_MUTED,
        font=(FONT_FAMILY, 13)
    )

    style.configure("Card.TFrame",
        background=BG_CARD,
        relief="flat",
        borderwidth=1
    )

    style.configure("CardTitle.TLabel",
        background=BG_CARD,
        foreground=FG_MAIN,
        font=(FONT_FAMILY, 13, "bold")
    )

    style.configure("Toolbar.TFrame",
        background=BG_MAIN
    )

    style.configure("Modern.TButton",
        background=ACCENT,
        foreground="white",
        borderwidth=0,
        focusthickness=0,
        focuscolor=ACCENT,
        padding=(14, 8),
        font=(FONT_FAMILY, 13, "bold")
    )
    style.map("Modern.TButton",
        background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)],
        foreground=[("disabled", "#94a3b8")]
    )

    style.configure("Secondary.TButton",
        background=BG_INPUT,
        foreground=FG_MAIN,
        borderwidth=0,
        padding=(12, 8),
        font=(FONT_FAMILY, 13)
    )
    style.map("Secondary.TButton",
        background=[("active", "#334155")]
    )

    style.configure("Modern.TEntry",
        fieldbackground=BG_INPUT,
        foreground=FG_MAIN,
        insertcolor=FG_MAIN,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=8
    )

    style.configure("Modern.TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_INPUT,
        foreground=FG_MAIN,
        arrowcolor=FG_MAIN,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=6
    )

    style.map("Modern.TCombobox",
        fieldbackground=[("readonly", BG_INPUT)],
        foreground=[("readonly", FG_MAIN)],
        background=[("readonly", BG_INPUT)]
    )

    style.configure("Modern.Treeview",
        background=BG_INPUT,
        foreground=FG_MAIN,
        fieldbackground=BG_INPUT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        rowheight=34,
        font=(FONT_FAMILY, 13)
    )
    style.map("Modern.Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", "white")]
    )

    style.configure("Modern.Treeview.Heading",
        background="#1e293b",
        foreground=FG_MAIN,
        borderwidth=0,
        font=(FONT_FAMILY, 13, "bold"),
        padding=(8, 10)
    )
    style.map("Modern.Treeview.Heading",
        background=[("active", "#334155")]
    )

    return style

def add_bug(conn, title, description, bug_type, artifact_type, reporter, date_found):
    title = title.strip()
    description = description.strip()
    bug_type = bug_type.strip()
    artifact_type = artifact_type.strip()
    reporter = reporter.strip()
    date_found = date_found.strip()

    if not title:
        raise ValueError("Title is required.")
    if not description:
        raise ValueError("Description is required.")
    if not bug_type:
        raise ValueError("Bug type is required.")
    if not artifact_type:
        raise ValueError("Artifact type is required.")
    if not reporter:
        raise ValueError("Reporter name is required.")
    if not date_found:
        raise ValueError("Date found is required.")

    try:
        y, m, d = map(int, date_found.split("-"))
        date(y, m, d)
    except Exception:
        raise ValueError("Date must be in YYYY-MM-DD format.")

    cur = conn.execute("""
        INSERT INTO bugs (
            title, description, bug_type, artifact_type,
            reporter, date_found, status, date_fixed
        )
        VALUES (?, ?, ?, ?, ?, ?, 'Open', NULL)
    """, (title, description, bug_type, artifact_type, reporter, date_found))
    conn.commit()
    return cur.lastrowid


def update_bug(conn, bug_id, title, description, bug_type, artifact_type, reporter, date_found):
    """
    Update editable bug fields.

    Raises:
        ValueError: if bug does not exist or fields are invalid
    """
    title = title.strip()
    description = description.strip()
    bug_type = bug_type.strip()
    artifact_type = artifact_type.strip()
    reporter = reporter.strip()
    date_found = date_found.strip()

    if not title:
        raise ValueError("Title is required.")
    if not description:
        raise ValueError("Description is required.")
    if not bug_type:
        raise ValueError("Bug type is required.")
    if not artifact_type:
        raise ValueError("Artifact type is required.")
    if not reporter:
        raise ValueError("Reporter name is required.")
    if not date_found:
        raise ValueError("Date found is required.")

    try:
        y, m, d = map(int, date_found.split("-"))
        date(y, m, d)
    except Exception:
        raise ValueError("Date must be in YYYY-MM-DD format.")

    cur = conn.execute("""
        UPDATE bugs
        SET title = ?, description = ?, bug_type = ?, artifact_type = ?,
            reporter = ?, date_found = ?
        WHERE id = ?
    """, (title, description, bug_type, artifact_type, reporter, date_found, bug_id))

    conn.commit()

    if cur.rowcount == 0:
        raise ValueError("Bug not found.")

def get_all_bugs(conn):
    return conn.execute("""
        SELECT id, title, artifact_type, status, bug_type, date_found
        FROM bugs
        ORDER BY date_found ASC, id ASC
    """).fetchall()

def get_bug_status(conn, bug_id):
    row = conn.execute("SELECT status FROM bugs WHERE id = ?", (bug_id,)).fetchone()
    if not row:
        raise ValueError("Bug not found.")
    return row[0]

def get_bug_by_id(conn, bug_id):
    return conn.execute("""
        SELECT id, title, description, bug_type, artifact_type, reporter, date_found, status, date_fixed
        FROM bugs
        WHERE id = ?
    """, (bug_id,)).fetchone()


def get_allowed_transitions(status):
    return sorted(TRANSITIONS.get(status, set()))

def delete_bug(conn, bug_id):
    """
    Delete a bug by ID.

    Raises:
        ValueError: if bug does not exist
    """
    cur = conn.execute("DELETE FROM bugs WHERE id = ?", (bug_id,))
    conn.commit()

    if cur.rowcount == 0:
        raise ValueError("Bug not found.")

def search_bug_by_id(conn, bug_id):
    """
    Return bug rows matching a specific ID.
    """
    return conn.execute("""
        SELECT id, title, artifact_type, status, bug_type, date_found
        FROM bugs
        WHERE id = ?
        ORDER BY date_found ASC, id ASC
    """, (bug_id,)).fetchall()

def search_bugs_by_keyword(conn, keyword):
    """
    Return bug rows where title or description contains the keyword.
    Case-insensitive.
    """
    keyword = f"%{keyword.strip()}%"
    return conn.execute("""
        SELECT id, title, artifact_type, status, bug_type, date_found
        FROM bugs
        WHERE title LIKE ? OR description LIKE ?
        ORDER BY date_found ASC, id ASC
    """, (keyword, keyword)).fetchall()

def get_distinct_artifacts(conn):
    """
    Return sorted distinct artifact types from the database.
    """
    rows = conn.execute("""
        SELECT DISTINCT artifact_type
        FROM bugs
        ORDER BY artifact_type ASC
    """).fetchall()
    return [row[0] for row in rows]

def filter_bugs(conn, status=None, artifact=None):
    """
    Return bugs filtered by status and/or artifact.
    If status/artifact is None or "All", that filter is ignored.
    """
    query = """
        SELECT id, title, artifact_type, status, bug_type, date_found
        FROM bugs
        WHERE 1=1
    """
    params = []

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if artifact and artifact != "All":
        query += " AND artifact_type = ?"
        params.append(artifact)

    query += " ORDER BY date_found ASC, id ASC"

    return conn.execute(query, params).fetchall()

def search_and_filter_bugs(conn, query="", status=None, artifact=None):
    """
    Combined search + filter.
    - If query is numeric, search by exact ID
    - Otherwise search title/description by keyword
    - Also apply status/artifact filters if not All
    """
    sql = """
        SELECT id, title, artifact_type, status, bug_type, date_found
        FROM bugs
        WHERE 1=1
    """
    params = []

    query = query.strip()

    if query:
        if query.isdigit():
            sql += " AND id = ?"
            params.append(int(query))
        else:
            sql += " AND (title LIKE ? OR description LIKE ?)"
            like_query = f"%{query}%"
            params.extend([like_query, like_query])

    if status and status != "All":
        sql += " AND status = ?"
        params.append(status)

    if artifact and artifact != "All":
        sql += " AND artifact_type = ?"
        params.append(artifact)

    sql += " ORDER BY date_found ASC, id ASC"

    return conn.execute(sql, params).fetchall()

def find_duplicate_bugs(conn, title, artifact_type):
    """
    Return possible duplicate bugs based on:
    - same artifact_type
    - similar title (case-insensitive LIKE)
    """
    title = title.strip()
    artifact_type = artifact_type.strip()

    if not title or not artifact_type:
        return []

    like_title = f"%{title}%"

    return conn.execute("""
        SELECT id, title, status
        FROM bugs
        WHERE artifact_type = ?
        AND LOWER(title) LIKE LOWER(?)
        ORDER BY id ASC
    """, (artifact_type, like_title)).fetchall()


def set_status(conn, bug_id, new_status):
    row = conn.execute("SELECT status FROM bugs WHERE id = ?", (bug_id,)).fetchone()
    if not row:
        raise ValueError("Bug not found.")

    current = row[0]
    if new_status not in TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transition: {current} -> {new_status}")

    date_fixed = None
    if new_status == "Fixed":
        date_fixed = today()

    conn.execute("""
        UPDATE bugs
        SET status = ?, date_fixed = COALESCE(?, date_fixed)
        WHERE id = ?
    """, (new_status, date_fixed, bug_id))
    conn.commit()
    return date_fixed


class BTRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BTR - Software Bug Tracker")
        self.root.geometry("900x500")

        self.conn = sqlite3.connect(DB)
        init_db(self.conn)

        self.build_ui()
        self.refresh_bug_table()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def make_popup(self, title, size="600x500"):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(size)
        win.minsize(620, 560)
        win.configure(bg=BG_MAIN)
        win.transient(self.root)

        container = ttk.Frame(win, style="Card.TFrame", padding=20)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        win.update_idletasks()
        win.geometry("")

        return win, container


    def make_text_widget(self, parent, width=40, height=6):
        text = tk.Text(
            parent,
            width=width,
            height=height,
            bg=BG_INPUT,
            fg=FG_MAIN,
            insertbackground=FG_MAIN,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            wrap="word",
            font=(FONT_FAMILY, 11)
        )
        return text

    
    def build_ui(self):
        header_frame = ttk.Frame(self.root, style="Toolbar.TFrame")
        header_frame.pack(fill="x", pady=(20, 12))

       
        inner_header = ttk.Frame(header_frame, style="Toolbar.TFrame")
        inner_header.pack(anchor="center")

        title = ttk.Label(
            inner_header,
            text="BTR - Software Bug Tracker",
            style="Title.TLabel"
        )
        title.pack(pady=(0, 8))

        button_frame = ttk.Frame(inner_header, style="Toolbar.TFrame")
        button_frame.pack()

        ttk.Button(
            button_frame,
            text="Add Bug",
            command=self.open_add_bug_window,
            style="Modern.TButton"
        ).pack(side="left", padx=6)

        ttk.Button(
            button_frame,
            text="Refresh",
            command=self.refresh_bug_table,
            style="Secondary.TButton"
        ).pack(side="left", padx=6)

        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=40, pady=(0, 12))

        control_card = ttk.Frame(self.root, style="Card.TFrame", padding=16)
        control_card.pack(fill="x", padx=20, pady=(0, 14))

        control_card.columnconfigure(0, weight=0)
        control_card.columnconfigure(1, weight=1)
        control_card.columnconfigure(2, weight=0)
        control_card.columnconfigure(3, weight=0)
        control_card.columnconfigure(4, weight=0)
        control_card.columnconfigure(5, weight=0)
        control_card.columnconfigure(6, weight=0)

        ttk.Label(control_card, text="").grid(row=1, column=0)

        ttk.Label(control_card, text="Search (Title/Desc)", style="CardTitle.TLabel").grid(
            row=1, column=1, sticky="w", padx=5, pady=(0, 6)
        )
        ttk.Label(control_card, text="Artifact", style="CardTitle.TLabel").grid(
            row=1, column=2, padx=5, pady=(0, 6)
        )
        ttk.Label(control_card, text="Status", style="CardTitle.TLabel").grid(
            row=1, column=3, padx=5, pady=(0, 6)
        )

        ttk.Label(control_card, text="").grid(row=2, column=0)

        self.search_entry = ttk.Entry(control_card, width=30, style="Modern.TEntry")
        self.search_entry.grid(row=2, column=1, padx=5, sticky="ew")
        self.search_entry.bind("<Return>", lambda e: self.apply_search_and_filters())
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_search_and_filters())

        self.artifact_filter = ttk.Combobox(
            control_card,
            values=["All"] + get_distinct_artifacts(self.conn),
            state="readonly",
            width=18,
            style="Modern.TCombobox"
        )
        self.artifact_filter.grid(row=2, column=2, padx=5)
        self.artifact_filter.set("All")
        self.artifact_filter.bind("<<ComboboxSelected>>", lambda e: self.apply_search_and_filters())

        self.status_filter = ttk.Combobox(
            control_card,
            values=["All"] + STATUSES,
            state="readonly",
            width=15,
            style="Modern.TCombobox"
        )
        self.status_filter.grid(row=2, column=3, padx=5)
        self.status_filter.set("All")
        self.status_filter.bind("<<ComboboxSelected>>", lambda e: self.apply_search_and_filters())

        ttk.Label(control_card, text="").grid(row=2, column=4)
        ttk.Label(control_card, text="").grid(row=2, column=5)

        ttk.Button(
            control_card,
            text="Clear",
            command=self.clear_search_and_filters,
            style="Secondary.TButton"
        ).grid(row=2, column=6, padx=5)

        table_card = ttk.Frame(self.root, style="Card.TFrame", padding=16)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ttk.Label(table_card, text="Bug List", style="CardTitle.TLabel").pack(
            anchor="w", pady=(0, 12)
        )

        table_frame = ttk.Frame(table_card, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        columns = ("ID", "Title", "Artifact", "Status", "Type", "Found")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Modern.Treeview"
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.column("ID", width=60, anchor="center")
        self.tree.column("Title", width=280, anchor="w")
        self.tree.column("Artifact", width=150, anchor="center")
        self.tree.column("Status", width=120, anchor="center")
        self.tree.column("Type", width=120, anchor="center")
        self.tree.column("Found", width=120, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<Double-1>", self.open_bug_details_from_event)

    def populate_tree(self, rows):
        for row in self.tree.get_children():
            self.tree.delete(row)

        # define colors once
        self.tree.tag_configure("evenrow", background="#172033")
        self.tree.tag_configure("oddrow", background="#1f2937")

        for i, bug in enumerate(rows):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=bug, tags=(tag,))

    def refresh_bug_table(self):
        rows = get_all_bugs(self.conn)
        self.populate_tree(rows)

        if hasattr(self, "artifact_filter"):
            self.refresh_artifact_filter()

    def refresh_artifact_filter(self):
        current = "All"
        if hasattr(self, "artifact_filter"):
            current = self.artifact_filter.get() or "All"

        values = ["All"] + get_distinct_artifacts(self.conn)
        self.artifact_filter["values"] = values

        if current in values:
            self.artifact_filter.set(current)
        else:
            self.artifact_filter.set("All")


    def apply_search_and_filters(self):
        query = self.search_entry.get().strip()
        status = self.status_filter.get()
        artifact = self.artifact_filter.get()

        rows = search_and_filter_bugs(
            self.conn,
            query=query,
            status=status,
            artifact=artifact
        )

        self.populate_tree(rows)


    def clear_search_and_filters(self):
        self.search_entry.delete(0, tk.END)
        self.status_filter.set("All")
        self.refresh_artifact_filter()
        self.artifact_filter.set("All")
        self.refresh_bug_table()
    
    def delete_bug_from_details(self, bug_id, detail_window):
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete Bug #{bug_id}?"
        )

        if not confirm:
            return

        try:
            delete_bug(self.conn, bug_id)
            messagebox.showinfo("Success", f"Bug #{bug_id} deleted successfully.")
            detail_window.destroy()
            self.refresh_bug_table()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def open_edit_bug_window(self, bug_id=None):
        if bug_id is None:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("No Selection", "Please select a bug from the table first.")
                return
            values = self.tree.item(selected[0], "values")
            bug_id = int(values[0])

        bug = get_bug_by_id(self.conn, bug_id)
        if not bug:
            messagebox.showerror("Error", "Bug not found.")
            return

        _, title, description, bug_type, artifact_type, reporter, date_found, status, date_fixed = bug

        win, container = self.make_popup(f"Edit Bug #{bug_id}", "620x560")

        ttk.Label(container, text=f"Edit Bug #{bug_id}", style="Title.TLabel").grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 6)
        )
        ttk.Label(container, text=f"Current Status: {status}", style="Subtitle.TLabel").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 16)
        )

        container.columnconfigure(1, weight=1)
        container.rowconfigure(3, weight=1)

        ttk.Label(container, text="Title", style="CardTitle.TLabel").grid(row=2, column=0, padx=8, pady=8, sticky="w")
        title_entry = ttk.Entry(container, width=40, style="Modern.TEntry")
        title_entry.grid(row=2, column=1, padx=8, pady=8, sticky="ew")
        title_entry.insert(0, title)

        ttk.Label(container, text="Description", style="CardTitle.TLabel").grid(row=3, column=0, padx=8, pady=8, sticky="nw")
        desc_text = self.make_text_widget(container, width=45, height=8)
        desc_text.grid(row=3, column=1, padx=8, pady=8, sticky="nsew")
        desc_text.insert("1.0", description)

        ttk.Label(container, text="Bug Type", style="CardTitle.TLabel").grid(row=4, column=0, padx=8, pady=8, sticky="w")
        bug_type_entry = ttk.Entry(container, width=40, style="Modern.TEntry")
        bug_type_entry.grid(row=4, column=1, padx=8, pady=8, sticky="ew")
        bug_type_entry.insert(0, bug_type)

        ttk.Label(container, text="Artifact Type", style="CardTitle.TLabel").grid(row=5, column=0, padx=8, pady=8, sticky="w")
        artifact_entry = ttk.Entry(container, width=40, style="Modern.TEntry")
        artifact_entry.grid(row=5, column=1, padx=8, pady=8, sticky="ew")
        artifact_entry.insert(0, artifact_type)

        ttk.Label(container, text="Reporter", style="CardTitle.TLabel").grid(row=6, column=0, padx=8, pady=8, sticky="w")
        reporter_entry = ttk.Entry(container, width=40, style="Modern.TEntry")
        reporter_entry.grid(row=6, column=1, padx=8, pady=8, sticky="ew")
        reporter_entry.insert(0, reporter)

        ttk.Label(container, text="Date Found", style="CardTitle.TLabel").grid(row=7, column=0, padx=8, pady=8, sticky="w")
        date_entry = ttk.Entry(container, width=40, style="Modern.TEntry")
        date_entry.grid(row=7, column=1, padx=8, pady=8, sticky="ew")
        date_entry.insert(0, date_found)

        def save_changes():
            try:
                update_bug(
                    self.conn,
                    bug_id,
                    title_entry.get(),
                    desc_text.get("1.0", "end").strip(),
                    bug_type_entry.get(),
                    artifact_entry.get(),
                    reporter_entry.get(),
                    date_entry.get(),
                )
                messagebox.showinfo("Success", f"Bug #{bug_id} updated successfully.")
                win.destroy()
                self.refresh_bug_table()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

        button_row = ttk.Frame(container, style="Toolbar.TFrame")
        button_row.grid(row=8, column=0, columnspan=2, pady=(18, 0))

        ttk.Button(button_row, text="Save Changes", command=save_changes, style="Modern.TButton").pack(side="left", padx=6)
        ttk.Button(button_row, text="Cancel", command=win.destroy, style="Secondary.TButton").pack(side="left", padx=6)

        
    def open_bug_details_from_event(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        bug_id = int(values[0])
        self.open_bug_details_window(bug_id)

   
    def open_bug_details_window(self, bug_id):
        bug = get_bug_by_id(self.conn, bug_id)
        if not bug:
            messagebox.showerror("Error", "Bug not found.")
            return

        _, title, description, bug_type, artifact_type, reporter, date_found, status, date_fixed = bug

        win, container = self.make_popup(f"Bug Details #{bug_id}", "650x560")

        ttk.Label(container, text=f"Bug #{bug_id}", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16)
        )

        container.columnconfigure(1, weight=1)
        container.rowconfigure(2, weight=1)

        details = [
            ("Title", title),
            ("Bug Type", bug_type),
            ("Artifact Type", artifact_type),
            ("Reporter", reporter),
            ("Date Found", date_found),
            ("Status", status),
            ("Date Fixed", date_fixed if date_fixed else "Not fixed yet"),
        ]

        row_idx = 1
        for label_text, value in details:
            ttk.Label(container, text=label_text, style="CardTitle.TLabel").grid(
                row=row_idx, column=0, padx=8, pady=8, sticky="nw"
            )
            ttk.Label(container, text=str(value), wraplength=380, style="Subtitle.TLabel").grid(
                row=row_idx, column=1, padx=8, pady=8, sticky="w"
            )
            row_idx += 1

        ttk.Label(container, text="Description", style="CardTitle.TLabel").grid(
            row=row_idx, column=0, padx=8, pady=8, sticky="nw"
        )
        text_widget = self.make_text_widget(container, width=48, height=10)
        text_widget.grid(row=row_idx, column=1, padx=8, pady=8, sticky="ew")
        text_widget.insert("1.0", description)
        text_widget.config(state="disabled")
        row_idx += 1

        button_frame = ttk.Frame(container, style="Toolbar.TFrame")
        button_frame.grid(row=row_idx, column=0, columnspan=2, pady=(18, 0))

        ttk.Button(
            button_frame,
            text="Edit Bug",
            command=lambda: [win.destroy(), self.open_edit_bug_window(bug_id)],
            style="Modern.TButton"
        ).pack(side="left", padx=6)

        ttk.Button(
            button_frame,
            text="Update Status",
            command=lambda: [win.destroy(), self.open_update_status_window(bug_id)],
            style="Secondary.TButton"
        ).pack(side="left", padx=6)

        ttk.Button(
            button_frame,
            text="Delete Bug",
            command=lambda: self.delete_bug_from_details(bug_id, win),
            style="Secondary.TButton"
        ).pack(side="left", padx=6)


    def open_add_bug_window(self):
        win, container = self.make_popup("Add Bug", "620x560")

        ttk.Label(container, text="Add New Bug", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16)
        )

        container.columnconfigure(1, weight=1)

        ttk.Label(container, text="Title", style="CardTitle.TLabel").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        title_entry = ttk.Entry(container, width=40, style="Modern.TEntry")
        title_entry.grid(row=1, column=1, padx=8, pady=8, sticky="ew")

        ttk.Label(container, text="Description", style="CardTitle.TLabel").grid(row=2, column=0, padx=8, pady=8, sticky="nw")
        desc_text = self.make_text_widget(container, width=45, height=8)
        desc_text.grid(row=2, column=1, padx=8, pady=8, sticky="nsew")

        ttk.Label(container, text="Bug Type", style="CardTitle.TLabel").grid(row=3, column=0, padx=8, pady=8, sticky="w")
        bug_type_entry = ttk.Entry(container, width=40, style="Modern.TEntry")
        bug_type_entry.grid(row=3, column=1, padx=8, pady=8, sticky="ew")

        ttk.Label(container, text="Artifact Type", style="CardTitle.TLabel").grid(row=4, column=0, padx=8, pady=8, sticky="w")
        artifact_entry = ttk.Entry(container, width=40, style="Modern.TEntry")
        artifact_entry.grid(row=4, column=1, padx=8, pady=8, sticky="ew")

        ttk.Label(container, text="Reporter", style="CardTitle.TLabel").grid(row=5, column=0, padx=8, pady=8, sticky="w")
        reporter_entry = ttk.Entry(container, width=40, style="Modern.TEntry")
        reporter_entry.grid(row=5, column=1, padx=8, pady=8, sticky="ew")

        ttk.Label(container, text="Date Found", style="CardTitle.TLabel").grid(row=6, column=0, padx=8, pady=8, sticky="w")
        date_entry = ttk.Entry(container, width=40, style="Modern.TEntry")
        date_entry.grid(row=6, column=1, padx=8, pady=8, sticky="ew")
        date_entry.insert(0, today())

        def submit():
            try:
                duplicates = find_duplicate_bugs(
                    self.conn,
                    title_entry.get(),
                    artifact_entry.get()
                )

                if duplicates:
                    msg = "Possible duplicate bugs found:\n\n"
                    for bug in duplicates:
                        msg += f"ID {bug[0]}: {bug[1]} ({bug[2]})\n"
                    msg += "\nDo you still want to create this bug?"

                    proceed = messagebox.askyesno("Duplicate Warning", msg)
                    if not proceed:
                        return

                bug_id = add_bug(
                    self.conn,
                    title_entry.get(),
                    desc_text.get("1.0", "end").strip(),
                    bug_type_entry.get(),
                    artifact_entry.get(),
                    reporter_entry.get(),
                    date_entry.get(),
                )
                messagebox.showinfo("Success", f"Bug added successfully.\nAssigned ID: {bug_id}")
                win.destroy()
                self.refresh_bug_table()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

        button_row = ttk.Frame(container, style="Toolbar.TFrame")
        button_row.grid(row=7, column=0, columnspan=2, pady=(18, 0))

        ttk.Button(button_row, text="Save Bug", command=submit, style="Modern.TButton").pack(side="left", padx=6)
        ttk.Button(button_row, text="Cancel", command=win.destroy, style="Secondary.TButton").pack(side="left", padx=6)


    def open_update_status_window(self, bug_id=None):
        if bug_id is None:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("No Selection", "Please select a bug from the table first.")
                return

            values = self.tree.item(selected[0], "values")
            bug_id = int(values[0])

        try:
            current_status = get_bug_status(self.conn, bug_id)
            allowed = get_allowed_transitions(current_status)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        if not allowed:
            messagebox.showinfo("Info", f"Bug {bug_id} is already '{current_status}'. No further transitions allowed.")
            return

        win, container = self.make_popup("Update Status", "420x260")

        ttk.Label(container, text=f"Update Status", style="Title.TLabel").pack(anchor="w", pady=(0, 10))
        ttk.Label(container, text=f"Bug ID: {bug_id}", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Label(container, text=f"Current Status: {current_status}", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 16))

        selected_status = tk.StringVar(value=allowed[0])
        combo = ttk.Combobox(
            container,
            textvariable=selected_status,
            values=allowed,
            state="readonly",
            style="Modern.TCombobox"
        )
        combo.pack(fill="x", pady=(0, 18))

        def submit():
            try:
                fix_date = set_status(self.conn, bug_id, selected_status.get())
                msg = f"Status updated to '{selected_status.get()}'."
                if fix_date:
                    msg += f"\nFix date recorded: {fix_date}"
                messagebox.showinfo("Success", msg)
                win.destroy()
                self.refresh_bug_table()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

        button_row = ttk.Frame(container, style="Toolbar.TFrame")
        button_row.pack()

        ttk.Button(button_row, text="Update", command=submit, style="Modern.TButton").pack(side="left", padx=6)
        ttk.Button(button_row, text="Cancel", command=win.destroy, style="Secondary.TButton").pack(side="left", padx=6)
            
    def on_close(self):
        self.conn.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    root.title("BTR - Software Bug Tracker")
    root.geometry("1100x700")
    root.minsize(950, 600)

    setup_modern_style(root)

    app = BTRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
