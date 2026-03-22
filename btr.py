#!/usr/bin/env python3
"""
BTR - Software Bug Tracker (Sprint 1)

A command-line bug tracking system with SQLite persistence.

Key Sprint 1 Features:
- Record a new bug (required fields enforced)
- View all bugs (sorted by date found and ID)
- Update lifecycle status (valid transitions only)
- Auto-record fix date when status becomes 'Fixed'
- Persistent storage in SQLite (btr.sqlite3)

Course: CPS406 (Winter 2026)
"""

import sqlite3                 # SQLite database engine (built into Python)
from datetime import date      # Used to generate today's date for date_fixed


# Database filename used for persistent storage
DB = "btr.sqlite3"


# ---- CLI Icons (for user-friendly output messages) ----
OK = "✔️"      # Indicates success
ERR = "✖️"     # Indicates an error
UPD = "🔄"     # Indicates an update action
INFO = "ℹ️"    # Indicates information message
WARN = "⚠️"    # Indicates warning (e.g., required field)
SAVE = "💾"    # Indicates data was saved/persisted


# Valid bug lifecycle statuses used in Sprint 1
STATUSES = ["Open", "In Progress", "Fixed", "Closed"]

# Valid transitions between statuses (business rules)
TRANSITIONS = {
    "Open": {"In Progress"},        # Only Open -> In Progress is allowed
    "In Progress": {"Fixed"},       # Only In Progress -> Fixed is allowed
    "Fixed": {"Closed"},            # Only Fixed -> Closed is allowed
    "Closed": set(),                # Closed is terminal state (no transitions)
}


def today():
    """Return today's date as a string in YYYY-MM-DD format."""
    return date.today().isoformat()


def init_db(conn):
    """
    Initialize database schema.
    Creates the 'bugs' table if it does not already exist.
    """
    conn.execute("""
    CREATE TABLE IF NOT EXISTS bugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique bug ID (auto-generated)
        title TEXT NOT NULL,                   -- Short bug title
        description TEXT NOT NULL,             -- Detailed bug description
        bug_type TEXT NOT NULL,                -- Bug category/type (UI/Logic/etc.)
        artifact_type TEXT NOT NULL,           -- Affected artifact (Source/Test/etc.)
        reporter TEXT NOT NULL,                -- Reporter name
        date_found TEXT NOT NULL,              -- Date discovered (YYYY-MM-DD)
        status TEXT NOT NULL,                  -- Lifecycle status
        date_fixed TEXT                        -- Date fixed (nullable)
    );
    """)
    conn.commit()  # Save schema changes


def read_nonempty(prompt):
    """
    Prompt user until a non-empty string is entered.
    Used for required text fields.
    """
    while True:
        s = input(prompt).strip()  # Remove whitespace
        if s:
            return s
        print(f"{WARN} Required field. Please enter a value.")


def read_date(prompt, default=None):
    """
    Prompt user for a valid date in YYYY-MM-DD format.
    If default is provided, pressing ENTER uses the default.
    """
    while True:
        # Show default date if provided
        s = input(f"{prompt} (YYYY-MM-DD){' ['+default+']' if default else ''}: ").strip()

        # Use default date if user presses enter
        if not s and default:
            return default

        try:
            # Validate date format by constructing a date object
            y, m, d = map(int, s.split("-"))
            date(y, m, d)
            return s
        except Exception:
            print(f"{ERR} Invalid date. Use YYYY-MM-DD.")


def choose(prompt, options):
    """
    Display a list of options and return the selected value.
    Used for choosing lifecycle status transitions.
    """
    print(prompt)

    # Print options with numeric indices
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")

    while True:
        s = input("Select: ").strip()
        # Only accept valid numbers in range
        if s.isdigit() and 1 <= int(s) <= len(options):
            return options[int(s) - 1]
        print(f"{ERR} Invalid selection. Try again.")


def create_bug(conn):
    """
    Record a new bug into the database.
    New bugs always start with status='Open' and date_fixed=NULL.
    """
    print("\n--- Record a New Bug ---")

    # Read required bug fields from user
    title = read_nonempty("Title: ")
    desc = read_nonempty("Description: ")
    bug_type = read_nonempty("Bug type (e.g., UI/Logic/Performance/Security/Other): ")
    artifact = read_nonempty("Artifact type (e.g., Source Code/Test File/Document/Binary/Data File): ")
    reporter = read_nonempty("Reporter name: ")

    # Date found uses today's date by default
    found = read_date("Date found", default=today())

    # Insert new bug into SQLite database
    cur = conn.execute("""
        INSERT INTO bugs (title, description, bug_type, artifact_type, reporter, date_found, status, date_fixed)
        VALUES (?, ?, ?, ?, ?, ?, 'Open', NULL)
    """, (title, desc, bug_type, artifact, reporter, found))

    conn.commit()  # Persist the record

    # Show confirmation and assigned auto-generated ID
    print(f"{OK} Bug recorded successfully. Assigned ID: {cur.lastrowid}")
    print(f"{SAVE} Saved to database: {DB}")


def list_bugs(conn):
    """
    Display all bugs in a table format.
    Sorted by date_found and ID for consistent viewing.
    """
    print("\n--- Bug List ---")

    # Query minimal summary fields for list view
    rows = conn.execute("""
        SELECT id, status, bug_type, date_found, title
        FROM bugs
        ORDER BY date_found ASC, id ASC
    """).fetchall()

    # If there are no records, display message and return
    if not rows:
        print(f"{INFO} No bugs recorded yet.")
        return

    # Print table header
    print("ID | Lifecycle     | Type        | Found      | Title")
    print("-" * 70)

    # Print each row in formatted layout
    for i, st, bt, df, ti in rows:
        print(f"{i:2d} | {st:<12} | {bt:<11} | {df} | {ti}")


# ---- Minimal business logic (testable) ----
def set_status(conn, bug_id: int, new_status: str):
    """
    Update bug status while enforcing valid lifecycle transitions.
    Automatically sets date_fixed when status becomes 'Fixed'.

    Raises:
        ValueError: if bug not found or invalid transition attempted
    """
    # Retrieve current status of the bug
    row = conn.execute("SELECT status FROM bugs WHERE id = ?", (bug_id,)).fetchone()
    if not row:
        raise ValueError("Bug not found.")

    current = row[0]

    # Check if requested transition is valid
    if new_status not in TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transition: {current} -> {new_status}")

    # Default: no fix date update
    date_fixed = None

    # If moving to Fixed, automatically record fix date
    if new_status == "Fixed":
        date_fixed = today()

    # Update the database record
    conn.execute("""
        UPDATE bugs
        SET status = ?, date_fixed = COALESCE(?, date_fixed)
        WHERE id = ?
    """, (new_status, date_fixed, bug_id))

    conn.commit()  # Persist update
    return date_fixed  # Return for CLI confirmation/tests


def update_status(conn):
    """
    CLI workflow for updating a bug’s lifecycle status.
    User enters bug ID, then selects next valid status.
    """
    print("\n--- Update Bug Lifecycle Status ---")
    bug_id = input("Bug ID: ").strip()

    # Validate bug ID format
    if not bug_id.isdigit():
        print(f"{ERR} Invalid Bug ID. Must be a number.")
        return

    bug_id = int(bug_id)

    # Retrieve current status
    row = conn.execute("SELECT status FROM bugs WHERE id = ?", (bug_id,)).fetchone()
    if not row:
        print(f"{ERR} Bug not found.")
        return

    current = row[0]

    # Compute allowed next statuses based on lifecycle rules
    allowed = sorted(TRANSITIONS.get(current, set()))
    if not allowed:
        print(f"{INFO} Bug {bug_id} is already '{current}'. No further transitions allowed.")
        return

    print(f"{INFO} Current lifecycle status: {current}")

    # Let user pick next allowed status
    new_status = choose("Select next lifecycle status (valid transitions only):", allowed)

    try:
        # Apply status update using testable core logic
        fix_date = set_status(conn, bug_id, new_status)
        print(f"{UPD} Lifecycle updated successfully.")

        # If bug became Fixed, show fix date message
        if new_status == "Fixed":
            print(f"{OK} Fix date automatically recorded: {fix_date}")

        print(f"{SAVE} Changes saved to database: {DB}")

    except ValueError as e:
        # Display error if invalid or bug missing
        print(f"{ERR} {e}")


def main():
    """
    Main program loop.
    Connects to database, initializes schema, and displays CLI menu.
    """
    conn = sqlite3.connect(DB)  # Create SQLite connection
    try:
        init_db(conn)  # Ensure required table exists

        # Loop until user chooses Exit
        while True:
            print("\n=========================")
            print(" BTR - Software Bug Tracker")
            print("=========================")
            print(f"{INFO} Database: {DB} (persistent storage enabled)")
            print("1) Record a new bug")
            print("2) View bug list")
            print("3) Update bug lifecycle status")
            print("0) Exit")

            choice = input("Select: ").strip()

            # Route menu options to correct feature
            if choice == "1":
                create_bug(conn)
            elif choice == "2":
                list_bugs(conn)
            elif choice == "3":
                update_status(conn)
            elif choice == "0":
                print(f"{OK} Goodbye.")
                break
            else:
                print(f"{ERR} Invalid selection.")
    finally:
        # Always close DB connection safely
        conn.close()


# Run main only when executed directly (not when imported for testing)
if __name__ == "__main__":
    main()
