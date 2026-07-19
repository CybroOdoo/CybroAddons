# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import base64
import csv
import io

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _csv_b64(*rows):
    """Encode a list-of-row-lists as base64 CSV bytes (comma-delimited)."""
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    return base64.b64encode(buf.getvalue().encode('utf-8'))


# v17 column layout: [seq, description, name]
HEADER = ['Sequence', 'Description', 'Name']


class TestImportWizardCsv(TransactionCase):
    """Tests for CSV import — action_import_task_checklist_csv()."""

    # ------------------------------------------------------------------
    # Fixtures
    # ------------------------------------------------------------------
    def setUp(self):
        super().setUp()
        self.Wizard    = self.env['import.task.checklist']
        self.Checklist = self.env['task.checklist']
        self.company   = self.env.company

    def _wizard(self, file_content, filename='test.csv', file_type='csv'):
        return self.Wizard.create({
            'file_type':     file_type,
            'file_content':  file_content,
            'filename':      filename,
        })

    # ------------------------------------------------------------------
    # Happy path — records created
    # ------------------------------------------------------------------
    def test_csv_creates_record_name_from_col2(self):
        """Record 'name' must be taken from column 2 (v17 layout)."""
        content = _csv_b64(
            HEADER,
            ['1', 'First Description', 'First Task Name'],
        )
        self._wizard(content).action_import_task_checklist_csv()
        rec = self.Checklist.search([('name', '=', 'First Task Name')])
        self.assertTrue(rec, "task.checklist record should be created with name from col 2.")

    def test_csv_stores_description_from_col1(self):
        """Record 'description' must be taken from column 1 (v17 layout)."""
        content = _csv_b64(
            HEADER,
            ['1', 'My Description', 'My Task'],
        )
        self._wizard(content).action_import_task_checklist_csv()
        rec = self.Checklist.search([('name', '=', 'My Task')])
        self.assertTrue(rec)
        self.assertEqual(
            rec.description, 'My Description',
            "description should come from col 1."
        )

    def test_csv_imports_multiple_rows(self):
        """All data rows (after header) should produce separate records."""
        content = _csv_b64(
            HEADER,
            ['1', 'Desc Alpha', 'Alpha'],
            ['2', 'Desc Beta',  'Beta'],
            ['3', 'Desc Gamma', 'Gamma'],
        )
        self._wizard(content).action_import_task_checklist_csv()
        for name in ['Alpha', 'Beta', 'Gamma']:
            rec = self.Checklist.search([('name', '=', name)])
            self.assertTrue(rec, f"'{name}' should have been created.")

    # ------------------------------------------------------------------
    # Return value contract
    # ------------------------------------------------------------------
    def test_csv_returns_client_action_notification(self):
        """Method must return an ir.actions.client display_notification dict."""
        content = _csv_b64(HEADER, ['1', 'Ret Desc', 'Ret Task'])
        result  = self._wizard(content).action_import_task_checklist_csv()
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'),  'display_notification')

    def test_csv_notification_type_is_success(self):
        """Notification params.type must be 'success' on valid import."""
        content = _csv_b64(HEADER, ['1', 'Succ Desc', 'Succ Task'])
        result  = self._wizard(content).action_import_task_checklist_csv()
        self.assertEqual(result['params']['type'], 'success')

    def test_csv_notification_not_sticky(self):
        """Success notification should not be sticky (auto-dismiss)."""
        content = _csv_b64(HEADER, ['1', 'Sticky Desc', 'Sticky Task'])
        result  = self._wizard(content).action_import_task_checklist_csv()
        self.assertFalse(
            result['params'].get('sticky'),
            "sticky should be False so the banner auto-dismisses."
        )

    # ------------------------------------------------------------------
    # Duplicate prevention (v17 logic: keyed on col 1 / description)
    # ------------------------------------------------------------------
    def test_csv_no_duplicate_on_reimport(self):
        """Re-importing identical rows must not create duplicate records."""
        content = _csv_b64(HEADER, ['1', 'Dup Desc', 'Dup Task'])
        self._wizard(content).action_import_task_checklist_csv()
        self._wizard(content).action_import_task_checklist_csv()
        matches = self.Checklist.search([('name', '=', 'Dup Task')])
        self.assertEqual(len(matches), 1, "Duplicate record must not be created on re-import.")

    def test_csv_second_row_with_same_name_skipped(self):
        """Two rows sharing the same name (col 2) — second must be skipped."""
        content = _csv_b64(
            HEADER,
            ['1', 'Desc One', 'Same Name'],
            ['2', 'Desc Two', 'Same Name'],   # same col-2 value → should be skipped
        )
        self._wizard(content).action_import_task_checklist_csv()
        # Only the first should exist; the second shares name with the first
        task_one = self.Checklist.search([('name', '=', 'Same Name'), ('description', '=', 'Desc One')])
        task_two = self.Checklist.search([('name', '=', 'Same Name'), ('description', '=', 'Desc Two')])
        self.assertTrue(task_one,  "First row should be created.")
        self.assertFalse(task_two, "Row with duplicate name (col 2) should be skipped.")

    # ------------------------------------------------------------------
    # Error cases
    # ------------------------------------------------------------------
    def test_csv_raises_on_invalid_content(self):
        """Non-CSV / undecodable content must raise UserError."""
        # raw binary that will fail utf-8 decode
        invalid = base64.b64encode(bytes(range(128, 200)))
        with self.assertRaises(UserError):
            self._wizard(invalid).action_import_task_checklist_csv()

    def test_csv_raises_on_empty_base64(self):
        """Empty base64 payload should raise UserError (bare except in v17)."""
        empty = base64.b64encode(b'')
        with self.assertRaises(UserError):
            self._wizard(empty).action_import_task_checklist_csv()

    def test_csv_raises_when_row_has_fewer_than_3_columns(self):
        """Row with fewer than 3 columns will cause index error → UserError."""
        content = _csv_b64(
            HEADER,
            ['only_one_col'],   # missing col 1 and col 2
        )
        with self.assertRaises(UserError):
            self._wizard(content).action_import_task_checklist_csv()

    # ------------------------------------------------------------------
    # Header-only (no data rows)
    # ------------------------------------------------------------------
    def test_csv_header_only_creates_no_records(self):
        """CSV with only the header row should raise UserError."""
        content      = _csv_b64(HEADER)
        with self.assertRaises(UserError):
            self._wizard(content).action_import_task_checklist_csv()

    # ------------------------------------------------------------------
    # Wizard fields
    # ------------------------------------------------------------------
    def test_wizard_default_file_type_is_csv(self):
        """Wizard file_type field should default to 'csv'."""
        content = _csv_b64(HEADER)
        wiz = self._wizard(content)
        self.assertEqual(wiz.file_type, 'csv')

    def test_wizard_company_id_defaults_to_current_company(self):
        """Wizard company_id should default to env.company."""
        content = _csv_b64(HEADER)
        wiz = self._wizard(content)
        self.assertEqual(wiz.company_id, self.company)

    def test_wizard_filename_stored(self):
        """Filename passed to wizard should be persisted."""
        content = _csv_b64(HEADER)
        wiz = self._wizard(content, filename='my_import.csv')
        self.assertEqual(wiz.filename, 'my_import.csv')
