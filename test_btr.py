"""
BTR - Software Bug Tracker (Sprint 1)
Unit Test Suite

Description:
This file contains automated unit tests for the Sprint 1
implementation of the BTR system (btr.py).

Testing Strategy:
- Uses Python's built-in unittest framework
- Uses a temporary SQLite database (test_btr.sqlite3)
- Ensures isolation between test cases
- Verifies lifecycle transitions and persistence behavior

How to Run:
    python3 -m unittest -v test_btr.py
"""

# Standard library imports
import os              # Used to remove temporary test database file
import sqlite3         # Used to connect to SQLite test database
import unittest        # Python built-in unit testing framework

# Import the module being tested
import btr


# Name of temporary database used ONLY for testing
TEST_DB = "test_btr.sqlite3"


# CLI-style icons for clearer test output
OK = "✔️"
ERR = "✖️"
INFO = "ℹ️"


class TestBTR(unittest.TestCase):
    """
    Test class for Sprint 1 functionality.

    Each test:
    - Creates a fresh database
    - Executes logic
    - Cleans up afterward
    """

    def setUp(self):
        """
        Runs before each test method.
        Creates a new test database to ensure isolation.
        """
        # Remove existing test DB if it exists
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        # Create new SQLite connection
        self.conn = sqlite3.connect(TEST_DB)

        # Initialize schema using application logic
        btr.init_db(self.conn)

        print(f"\n{INFO} Setting up test database: {TEST_DB}")

    def tearDown(self):
        """
        Runs after each test method.
        Closes connection and deletes temporary database file.
        """
        self.conn.close()

        # Remove test database file to reset environment
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        print(f"{INFO} Test database removed.\n")

    def _insert_open_bug(self):
        """
        Helper function to insert a default bug
        with lifecycle status = 'Open'.

        Returns:
            int: Newly created bug ID
        """
        cur = self.conn.execute("""
            INSERT INTO bugs (
                title, description, bug_type, artifact_type,
                reporter, date_found, status, date_fixed
            )
            VALUES (?, ?, ?, ?, ?, ?, 'Open', NULL)
        """, (
            "Login fails",          # title
            "Cannot login",         # description
            "Logic",                # bug_type
            "Source Code",          # artifact_type
            "QA",                   # reporter
            "2026-02-01"            # date_found
        ))

        self.conn.commit()  # Persist insertion
        return cur.lastrowid  # Return generated bug ID

    def test_create_bug_defaults(self):
        """
        TC-01:
        Verify that newly created bug:
        - Has status 'Open'
        - Has date_fixed = NULL
        """
        bug_id = self._insert_open_bug()

        # Retrieve inserted record
        status, date_fixed = self.conn.execute(
            "SELECT status, date_fixed FROM bugs WHERE id=?",
            (bug_id,)
        ).fetchone()

        # Assertions
        self.assertEqual(status, "Open")
        self.assertIsNone(date_fixed)

        print(f"{OK} TC-01 Passed: Bug created with default status 'Open' and date_fixed NULL.")

    def test_persistence_restart(self):
        """
        TC-02:
        Verify that data persists after closing and reopening the database.
        """
        self._insert_open_bug()

        # Simulate application restart
        self.conn.close()
        self.conn = sqlite3.connect(TEST_DB)

        # Count number of bug records
        count = self.conn.execute("SELECT COUNT(*) FROM bugs").fetchone()[0]

        self.assertEqual(count, 1)

        print(f"{OK} TC-02 Passed: Bug record persisted after database restart.")

    def test_valid_transition_sets_fix_date(self):
        """
        TC-03:
        Verify valid lifecycle transitions:
        Open → In Progress → Fixed
        and confirm fix date is automatically recorded.
        """
        bug_id = self._insert_open_bug()

        # Perform valid transitions using business logic
        btr.set_status(self.conn, bug_id, "In Progress")
        fix_date = btr.set_status(self.conn, bug_id, "Fixed")

        # Retrieve updated record
        status, date_fixed = self.conn.execute(
            "SELECT status, date_fixed FROM bugs WHERE id=?",
            (bug_id,)
        ).fetchone()

        # Assertions
        self.assertEqual(status, "Fixed")
        self.assertIsNotNone(date_fixed)
        self.assertEqual(date_fixed, fix_date)

        print(f"{OK} TC-03 Passed: Valid transition Open → In Progress → Fixed recorded fix date automatically.")

    def test_invalid_transition_rejected(self):
        """
        TC-04:
        Verify invalid lifecycle transition is rejected.
        Example: Open → Fixed (skipping In Progress).
        """
        bug_id = self._insert_open_bug()

        # Expect ValueError for invalid transition
        with self.assertRaises(ValueError):
            btr.set_status(self.conn, bug_id, "Fixed")

        print(f"{OK} TC-04 Passed: Invalid transition Open → Fixed rejected correctly.")


# Entry point for running tests directly
if __name__ == "__main__":
    print(f"{INFO} Running BTR Sprint 1 Unit Tests...\n")
    unittest.main(verbosity=2)
