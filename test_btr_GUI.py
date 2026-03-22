# Not testing the GUI but just general functionality of the app.

"""
BTR - Software Bug Tracker
Full Unit Test Suite

Description:
This file contains automated unit tests for the BTR system.

Testing Strategy:
- Uses Python's built-in unittest framework
- Uses a temporary SQLite database (test_btr.sqlite3)
- Ensures isolation between test cases
- Verifies CRUD operations, lifecycle transitions,
  search, filtering, duplicate detection, and persistence

How to Run:
    python3 -m unittest -v test_btr_GUI.py
"""

import os
import sqlite3
import unittest


import btr_GUI as btr


TEST_DB = "test_btr.sqlite3"

OK = "✔️"
INFO = "ℹ️"


class TestBTR(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        self.conn = sqlite3.connect(TEST_DB)
        btr.init_db(self.conn)

        print(f"\n{INFO} Setting up test database: {TEST_DB}")

    def tearDown(self):
        self.conn.close()

        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

        print(f"{INFO} Test database removed.\n")

    def _add_sample_bug(
        self,
        title="Login fails",
        description="Cannot login with valid credentials",
        bug_type="Logic",
        artifact_type="Source Code",
        reporter="QA",
        date_found="2026-03-18",
    ):
        return btr.add_bug(
            self.conn,
            title,
            description,
            bug_type,
            artifact_type,
            reporter,
            date_found,
        )

    # -------------------------------
    # Creation / validation
    # -------------------------------

    def test_add_bug_defaults(self):
        bug_id = self._add_sample_bug()

        row = self.conn.execute(
            "SELECT status, date_fixed FROM bugs WHERE id = ?",
            (bug_id,)
        ).fetchone()

        self.assertEqual(row[0], "Open")
        self.assertIsNone(row[1])

        print(f"{OK} TC-01 Passed: New bug defaults to Open and date_fixed is NULL.")

    def test_add_bug_generates_id(self):
        bug_id = self._add_sample_bug()
        self.assertIsInstance(bug_id, int)
        self.assertGreater(bug_id, 0)

        print(f"{OK} TC-02 Passed: Bug ID generated automatically.")

    def test_add_bug_empty_title_rejected(self):
        with self.assertRaises(ValueError):
            btr.add_bug(
                self.conn,
                "",
                "desc",
                "Logic",
                "Source Code",
                "QA",
                "2026-03-18",
            )

        print(f"{OK} TC-03 Passed: Empty title rejected.")

    def test_add_bug_empty_description_rejected(self):
        with self.assertRaises(ValueError):
            btr.add_bug(
                self.conn,
                "Login fails",
                "",
                "Logic",
                "Source Code",
                "QA",
                "2026-03-18",
            )

        print(f"{OK} TC-04 Passed: Empty description rejected.")

    def test_add_bug_invalid_date_rejected(self):
        with self.assertRaises(ValueError):
            btr.add_bug(
                self.conn,
                "Login fails",
                "desc",
                "Logic",
                "Source Code",
                "QA",
                "2026-99-99",
            )

        print(f"{OK} TC-05 Passed: Invalid date rejected.")

    # -------------------------------
    # Persistence
    # -------------------------------

    def test_persistence_restart(self):
        self._add_sample_bug()

        self.conn.close()
        self.conn = sqlite3.connect(TEST_DB)

        count = self.conn.execute("SELECT COUNT(*) FROM bugs").fetchone()[0]
        self.assertEqual(count, 1)

        print(f"{OK} TC-06 Passed: Data persists after restart.")

    # -------------------------------
    # Viewing / retrieval
    # -------------------------------

    def test_get_bug_by_id_valid(self):
        bug_id = self._add_sample_bug()
        bug = btr.get_bug_by_id(self.conn, bug_id)

        self.assertIsNotNone(bug)
        self.assertEqual(bug[0], bug_id)
        self.assertEqual(bug[1], "Login fails")

        print(f"{OK} TC-07 Passed: Valid bug retrieved by ID.")

    def test_get_bug_by_id_invalid(self):
        bug = btr.get_bug_by_id(self.conn, 9999)
        self.assertIsNone(bug)

        print(f"{OK} TC-08 Passed: Invalid bug ID returns None.")

    def test_get_all_bugs(self):
        self._add_sample_bug()
        self._add_sample_bug(
            title="Crash on save",
            description="App crashes on save button",
            bug_type="UI",
            artifact_type="Document",
            reporter="Tester",
            date_found="2026-03-19",
        )

        bugs = btr.get_all_bugs(self.conn)
        self.assertEqual(len(bugs), 2)

        print(f"{OK} TC-09 Passed: Bug listing returns all bugs.")

    # -------------------------------
    # Editing
    # -------------------------------

    def test_update_bug_success(self):
        bug_id = self._add_sample_bug()

        btr.update_bug(
            self.conn,
            bug_id,
            "Login broken",
            "Updated description",
            "Security",
            "Source Code",
            "Dev",
            "2026-03-20",
        )

        bug = btr.get_bug_by_id(self.conn, bug_id)
        self.assertEqual(bug[1], "Login broken")
        self.assertEqual(bug[2], "Updated description")
        self.assertEqual(bug[3], "Security")
        self.assertEqual(bug[5], "Dev")
        self.assertEqual(bug[6], "2026-03-20")

        print(f"{OK} TC-10 Passed: Bug updated successfully.")

    def test_update_bug_invalid_id(self):
        with self.assertRaises(ValueError):
            btr.update_bug(
                self.conn,
                9999,
                "Title",
                "Desc",
                "Logic",
                "Source Code",
                "QA",
                "2026-03-18",
            )

        print(f"{OK} TC-11 Passed: Editing invalid bug rejected.")

    # -------------------------------
    # Deletion
    # -------------------------------

    def test_delete_bug_success(self):
        bug_id = self._add_sample_bug()
        btr.delete_bug(self.conn, bug_id)

        bug = btr.get_bug_by_id(self.conn, bug_id)
        self.assertIsNone(bug)

        print(f"{OK} TC-12 Passed: Bug deleted successfully.")

    def test_delete_bug_invalid_id(self):
        with self.assertRaises(ValueError):
            btr.delete_bug(self.conn, 9999)

        print(f"{OK} TC-13 Passed: Deleting invalid bug rejected.")

    # -------------------------------
    # Lifecycle status
    # -------------------------------

    def test_valid_transition_sets_fix_date(self):
        bug_id = self._add_sample_bug()

        btr.set_status(self.conn, bug_id, "In Progress")
        fix_date = btr.set_status(self.conn, bug_id, "Fixed")

        row = self.conn.execute(
            "SELECT status, date_fixed FROM bugs WHERE id = ?",
            (bug_id,)
        ).fetchone()

        self.assertEqual(row[0], "Fixed")
        self.assertEqual(row[1], fix_date)
        self.assertIsNotNone(row[1])

        print(f"{OK} TC-14 Passed: Valid status transition records fix date.")

    def test_invalid_transition_rejected(self):
        bug_id = self._add_sample_bug()

        with self.assertRaises(ValueError):
            btr.set_status(self.conn, bug_id, "Fixed")

        print(f"{OK} TC-15 Passed: Invalid transition rejected.")

    def test_closed_is_terminal(self):
        bug_id = self._add_sample_bug()

        btr.set_status(self.conn, bug_id, "In Progress")
        btr.set_status(self.conn, bug_id, "Fixed")
        btr.set_status(self.conn, bug_id, "Closed")

        with self.assertRaises(ValueError):
            btr.set_status(self.conn, bug_id, "In Progress")

        print(f"{OK} TC-16 Passed: Closed status is terminal.")

    def test_get_bug_status(self):
        bug_id = self._add_sample_bug()
        status = btr.get_bug_status(self.conn, bug_id)

        self.assertEqual(status, "Open")

        print(f"{OK} TC-17 Passed: Current bug status retrieved correctly.")

    def test_get_allowed_transitions(self):
        allowed = btr.get_allowed_transitions("Open")
        self.assertEqual(allowed, ["In Progress"])

        print(f"{OK} TC-18 Passed: Allowed transitions returned correctly.")

    # -------------------------------
    # Search
    # -------------------------------

    def test_search_bug_by_id_found(self):
        bug_id = self._add_sample_bug()
        rows = btr.search_bug_by_id(self.conn, bug_id)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], bug_id)

        print(f"{OK} TC-19 Passed: Search by ID returns matching bug.")

    def test_search_bug_by_id_not_found(self):
        rows = btr.search_bug_by_id(self.conn, 9999)
        self.assertEqual(rows, [])

        print(f"{OK} TC-20 Passed: Search by invalid ID returns no results.")

    def test_search_bugs_by_keyword_found(self):
        self._add_sample_bug(
            title="Login fails",
            description="Cannot login with valid credentials"
        )
        self._add_sample_bug(
            title="Crash on save",
            description="Application crashes when saving"
        )

        rows = btr.search_bugs_by_keyword(self.conn, "login")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "Login fails")

        print(f"{OK} TC-21 Passed: Keyword search returns matching bug.")

    def test_search_bugs_by_keyword_no_result(self):
        self._add_sample_bug()
        rows = btr.search_bugs_by_keyword(self.conn, "network")
        self.assertEqual(rows, [])

        print(f"{OK} TC-22 Passed: Keyword search with no match returns empty list.")

    # -------------------------------
    # Filtering
    # -------------------------------

    def test_filter_bugs_by_status(self):
        id1 = self._add_sample_bug(title="Bug A")
        id2 = self._add_sample_bug(title="Bug B")
        btr.set_status(self.conn, id2, "In Progress")

        rows = btr.filter_bugs(self.conn, status="In Progress", artifact="All")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], id2)

        print(f"{OK} TC-23 Passed: Status filter works correctly.")

    def test_filter_bugs_by_artifact(self):
        self._add_sample_bug(title="Bug A", artifact_type="Source Code")
        self._add_sample_bug(title="Bug B", artifact_type="Document")

        rows = btr.filter_bugs(self.conn, status="All", artifact="Document")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], "Document")

        print(f"{OK} TC-24 Passed: Artifact filter works correctly.")

    def test_filter_bugs_by_status_and_artifact(self):
        self._add_sample_bug(title="Bug A", artifact_type="Source Code")
        id2 = self._add_sample_bug(title="Bug B", artifact_type="Document")
        btr.set_status(self.conn, id2, "In Progress")

        rows = btr.filter_bugs(self.conn, status="In Progress", artifact="Document")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], id2)

        print(f"{OK} TC-25 Passed: Combined status + artifact filter works correctly.")

    def test_get_distinct_artifacts(self):
        self._add_sample_bug(title="Bug A", artifact_type="Source Code")
        self._add_sample_bug(title="Bug B", artifact_type="Document")
        self._add_sample_bug(title="Bug C", artifact_type="Source Code")

        artifacts = btr.get_distinct_artifacts(self.conn)

        self.assertEqual(artifacts, ["Document", "Source Code"])

        print(f"{OK} TC-26 Passed: Distinct artifact list returned correctly.")

    # -------------------------------
    # Combined search + filter
    # -------------------------------

    def test_search_and_filter_bugs(self):
        self._add_sample_bug(
            title="Login fails",
            description="Cannot login",
            artifact_type="Source Code"
        )
        id2 = self._add_sample_bug(
            title="Login page broken",
            description="UI issue",
            artifact_type="Document"
        )
        btr.set_status(self.conn, id2, "In Progress")

        rows = btr.search_and_filter_bugs(
            self.conn,
            query="login",
            status="In Progress",
            artifact="Document"
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], id2)

        print(f"{OK} TC-27 Passed: Combined search + filter works correctly.")

    # -------------------------------
    # Duplicate detection
    # -------------------------------

    def test_find_duplicate_bugs_found(self):
        self._add_sample_bug(
            title="Login fails on submit",
            artifact_type="Source Code"
        )

        duplicates = btr.find_duplicate_bugs(
            self.conn,
            "Login fails",
            "Source Code"
        )

        self.assertEqual(len(duplicates), 1)
        self.assertIn("Login fails", duplicates[0][1])

        print(f"{OK} TC-28 Passed: Duplicate detection finds similar title on same artifact.")

    def test_find_duplicate_bugs_not_found_different_artifact(self):
        self._add_sample_bug(
            title="Login fails on submit",
            artifact_type="Document"
        )

        duplicates = btr.find_duplicate_bugs(
            self.conn,
            "Login fails",
            "Source Code"
        )

        self.assertEqual(duplicates, [])

        print(f"{OK} TC-29 Passed: Duplicate detection ignores different artifact.")

    def test_find_duplicate_bugs_empty_input(self):
        duplicates = btr.find_duplicate_bugs(self.conn, "", "")
        self.assertEqual(duplicates, [])

        print(f"{OK} TC-30 Passed: Duplicate detection handles empty input safely.")


if __name__ == "__main__":
    print(f"{INFO} Running BTR Full Unit Tests...\n")
    unittest.main(verbosity=2)
