# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Syamili K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "chatter_activity_delay")
class TestActivityDelayFeedbackLogic(TransactionCase):
    """
    Unit tests for the delay-notice logic.

    The JS patch checks `state === 'overdue'` and builds a feedback string.
    These tests mirror that logic in Python so the behaviour can be validated
    server-side (e.g. via `mail.message` body content) and to document
    expected outcomes clearly.
    """

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _build_delayed_feedback(existing_feedback, due_date: str, done_date: str) -> str:
        """
        Replicate the JS feedback-building logic exactly.

        JS (no prior feedback):
            feedback = "DELAYED\\nDue Date :" + dueDate + "\\nActivity Done Date:  " + doneDate
        JS (with prior feedback):
            feedback = existing + "\\nDELAYED\\nDue Date :" + dueDate + ...
        """
        suffix = f"\nDELAYED\nDue Date :{due_date}\nActivity Done Date:  {done_date}"
        if existing_feedback is not None:
            return existing_feedback + suffix
        return f"DELAYED\nDue Date :{due_date}\nActivity Done Date:  {done_date}"

    @staticmethod
    def _is_overdue(deadline: date) -> bool:
        """Mirror the Odoo activity state logic for 'overdue'."""
        return deadline < date.today()

    # ── Tests: feedback text construction ─────────────────────────────────

    def test_01_overdue_no_prior_feedback_starts_with_delayed(self):
        """
        TEST 1 — Overdue, no prior feedback.
        Feedback must start with 'DELAYED'.
        """
        due = (date.today() - timedelta(days=3)).isoformat()
        done = date.today().isoformat()

        result = self._build_delayed_feedback(None, due, done)

        self.assertTrue(
            result.startswith("DELAYED"),
            "Feedback must start with 'DELAYED' when no prior feedback exists.",
        )

    def test_02_overdue_no_prior_feedback_contains_due_and_done_dates(self):
        """
        TEST 2 — Overdue, no prior feedback.
        Both Due Date and Activity Done Date must appear.
        """
        due = (date.today() - timedelta(days=5)).isoformat()
        done = date.today().isoformat()

        result = self._build_delayed_feedback(None, due, done)

        self.assertIn("Due Date :", result)
        self.assertIn("Activity Done Date:", result)
        self.assertIn(due, result)
        self.assertIn(done, result)

    def test_03_overdue_with_prior_feedback_appends_delay_notice(self):
        """
        TEST 3 — Overdue, with existing feedback text.
        The original feedback must be preserved and DELAYED appended.
        """
        due = (date.today() - timedelta(days=2)).isoformat()
        done = date.today().isoformat()
        original = "Spoke with the client and resolved the issue."

        result = self._build_delayed_feedback(original, due, done)

        self.assertIn(original, result)
        self.assertIn("DELAYED", result)
        # Original text should come BEFORE the delay block
        self.assertLess(result.index(original), result.index("DELAYED"))

    def test_04_not_overdue_feedback_unchanged(self):
        """
        TEST 4 — Non-overdue activity ('planned' or 'today').
        No DELAYED text should ever be added.
        """
        due_future = (date.today() + timedelta(days=3)).isoformat()

        # simulate: state != 'overdue', so the if-block is skipped
        is_overdue = self._is_overdue(date.today() + timedelta(days=3))
        feedback = None

        if is_overdue:
            feedback = self._build_delayed_feedback(None, due_future, date.today().isoformat())

        self.assertIsNone(feedback, "Feedback must not be modified for non-overdue activities.")

    def test_05_today_activity_is_not_overdue(self):
        """
        TEST 5 — Activity due today is NOT considered overdue.
        """
        self.assertFalse(
            self._is_overdue(date.today()),
            "Due-today activity must not be overdue.",
        )

    def test_06_past_deadline_is_overdue(self):
        """
        TEST 6 — Activity with a deadline in the past IS overdue.
        """
        self.assertTrue(
            self._is_overdue(date.today() - timedelta(days=1)),
            "Deadline yesterday must be overdue.",
        )

    def test_07_done_date_is_today(self):
        """
        TEST 7 — Done date in feedback always equals today's ISO date.
        """
        due = (date.today() - timedelta(days=7)).isoformat()
        done = date.today().isoformat()

        result = self._build_delayed_feedback(None, due, done)

        self.assertIn(done, result)

    def test_08_feedback_format_newlines(self):
        """
        TEST 8 — Verify exact newline structure of the DELAYED block.
        Expected (no prior feedback):
            DELAYED
            Due Date :<date>
            Activity Done Date:  <date>
        """
        due = "2025-01-10"
        done = "2025-01-15"

        result = self._build_delayed_feedback(None, due, done)
        lines = result.split("\n")

        self.assertEqual(lines[0], "DELAYED")
        self.assertTrue(lines[1].startswith("Due Date :"))
        self.assertTrue(lines[2].startswith("Activity Done Date:"))

    def test_09_feedback_format_with_prior_text(self):
        """
        TEST 9 — When prior feedback exists, the DELAYED section is appended
        after a newline separator.
        """
        due = "2025-01-10"
        done = "2025-01-15"
        prior = "Initial notes."

        result = self._build_delayed_feedback(prior, due, done)
        lines = result.split("\n")

        # line 0: prior text
        self.assertEqual(lines[0], "Initial notes.")
        # line 1: DELAYED
        self.assertEqual(lines[1], "DELAYED")

    def test_10_empty_string_feedback_treated_as_existing(self):
        """
        TEST 10 — Empty string feedback is NOT undefined/None; the JS check
        `feedback != undefined` is True for '' in JS (empty string is defined).
        So existing empty string causes the suffix to be appended, not replaced.
        """
        # In JS: '' != undefined → True → append path
        due = "2025-03-01"
        done = "2025-03-10"

        result = self._build_delayed_feedback("", due, done)

        # Result begins with "" + suffix → starts with \n
        self.assertTrue(result.startswith("\nDELAYED"))
