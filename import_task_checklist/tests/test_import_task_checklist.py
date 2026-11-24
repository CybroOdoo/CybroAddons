# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64
import io
import openpyxl

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.import_task_checklist.wizards.import_task_checklist import ImportTaskCheckList


def create_test_xlsx_base64(rows):
    """Utility to generate an in-memory XLSX file encoded as base64 string"""
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    output = io.BytesIO()
    workbook.save(output)
    return base64.b64encode(output.getvalue()).decode('utf-8')


@tagged('post_install', '-at_install')
class TestImportTaskChecklist(TransactionCase):
    """Unit tests for import.task.checklist model and functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['import.task.checklist']
        cls.Checklist = cls.env['task.checklist']
        cls.ChecklistItem = cls.env['checklist.item']
        cls.company = cls.env.company

    def setUp(self):
        super().setUp()
        self.wizard = self.Wizard.create({
            'file_type': 'csv',
            'company_id': self.company.id,
            'filename': 'test_checklist.csv',
            'file_content': base64.b64encode(b'placeholder').decode('utf-8'),
        })

    def test__get_file_bytes(self):
        """Test _get_file_bytes function with various data types."""
        # 1. Empty content returns empty bytes
        self.wizard.file_content = False
        self.assertEqual(self.wizard._get_file_bytes(), b'')

        # 2. Base64-encoded string content
        original_bytes = b"Sample Checklist Content"
        self.wizard.file_content = base64.b64encode(original_bytes).decode('utf-8')
        self.assertEqual(self.wizard._get_file_bytes(), original_bytes)

        # 3. Object with .content attribute
        class DummyBinary:
            content = b"Content attribute bytes"
        dummy_wizard_content = type('DummyWizard', (), {'file_content': DummyBinary()})()
        self.assertEqual(ImportTaskCheckList._get_file_bytes(dummy_wizard_content), b"Content attribute bytes")

        # 4. Raw bytes on dummy object
        dummy_wizard_raw = type('DummyWizard', (), {'file_content': b"Raw bytes content"})()
        self.assertEqual(ImportTaskCheckList._get_file_bytes(dummy_wizard_raw), b"Raw bytes content")

        # 5. Plain non-base64 string content fallback
        dummy_wizard_str = type('DummyWizard', (), {'file_content': "Plain text string"})()
        self.assertEqual(ImportTaskCheckList._get_file_bytes(dummy_wizard_str), b"Plain text string")

    def test_get_file_bytes(self):
        """Alias test for _get_file_bytes function."""
        self.test__get_file_bytes()

    def test__get_file_text(self):
        """Test _get_file_text function with UTF-8 and BOM decoded text."""
        # 1. Empty content
        self.wizard.file_content = False
        self.assertEqual(self.wizard._get_file_text(), '')

        # 2. Normal text
        text_content = "Name,Description,Item Name,Item Description\nTask 1,Desc 1,Item 1,Detail 1"
        self.wizard.file_content = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
        self.assertEqual(self.wizard._get_file_text(), text_content)

        # 3. Text with UTF-8-SIG (BOM)
        bom_bytes = b'\xef\xbb\xbf' + text_content.encode('utf-8')
        self.wizard.file_content = base64.b64encode(bom_bytes).decode('utf-8')
        self.assertEqual(self.wizard._get_file_text(), text_content)

    def test_get_file_text(self):
        """Alias test for _get_file_text function."""
        self.test__get_file_text()

    def test__process_import_rows(self):
        """Test _process_import_rows function with valid, duplicate, and invalid rows."""
        # 1. Empty rows raises UserError
        with self.assertRaises(UserError) as cm:
            self.wizard._process_import_rows([])
        self.assertIn("The uploaded file is empty", str(cm.exception))

        # 2. Valid header and rows creation
        unique_name = "Sprint Setup Checklist"
        rows = [
            ["Checklist Name", "Description", "Checklist Item", "Item Description"],
            [unique_name, "Sprint Preparation", "Review Backlog", "Review tickets in backlog"],
            [unique_name, "Sprint Preparation", "Assign Roles", "Assign scrum master and testers"],
        ]

        result = self.wizard._process_import_rows(rows)
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'display_notification')
        self.assertEqual(result.get('params', {}).get('type'), 'success')

        checklist = self.Checklist.search([('name', '=', unique_name), ('company_id', '=', self.company.id)], limit=1)
        self.assertTrue(checklist, "Task checklist record should be created")
        self.assertEqual(checklist.description, "Sprint Preparation")
        self.assertEqual(len(checklist.checklist_ids), 2, "Two checklist items should be linked")

        # 3. Duplicate rows returns warning notification
        duplicate_result = self.wizard._process_import_rows(rows)
        self.assertEqual(duplicate_result.get('params', {}).get('type'), 'warning')

        # 4. No valid records found raises UserError
        with self.assertRaises(UserError) as cm:
            self.wizard._process_import_rows([["Checklist Name", "Description"], ["", ""]])
        self.assertIn("No valid task checklist records found", str(cm.exception))

        # 5. Fallback without headers (positional column indexes without matching header keywords)
        pos_name = "Sprint Alpha Release"
        pos_rows = [
            [pos_name, "Prepare and verify build", "Docker containers", "Verify container images"],
        ]
        pos_result = self.wizard._process_import_rows(pos_rows)
        self.assertEqual(pos_result.get('params', {}).get('type'), 'success')
        pos_chk = self.Checklist.search([('name', '=', pos_name)], limit=1)
        self.assertTrue(pos_chk)
        self.assertEqual(pos_chk.description, "Prepare and verify build")

    def test_process_import_rows(self):
        """Alias test for _process_import_rows function."""
        self.test__process_import_rows()

    def test_action_import_task_checklist_xlsx(self):
        """Test action_import_task_checklist_xlsx with valid and invalid files."""
        # 1. Invalid file extension
        self.wizard.filename = "wrong_extension.csv"
        with self.assertRaises(UserError) as cm:
            self.wizard.action_import_task_checklist_xlsx()
        self.assertIn("Invalid file format", str(cm.exception))

        # 2. Empty file content
        self.wizard.filename = "valid_empty.xlsx"
        self.wizard.file_content = False
        with self.assertRaises(UserError) as cm:
            self.wizard.action_import_task_checklist_xlsx()
        self.assertIn("The uploaded file is empty or missing content", str(cm.exception))

        # 3. Valid XLSX import
        unique_name = "XLSX Deployment Checklist"
        xlsx_rows = [
            ["Checklist Name", "Description", "Checklist Item", "Item Description"],
            [unique_name, "Deployment Tasks", "Run Migrations", "Apply Odoo database migrations"],
            [unique_name, "Deployment Tasks", "Restart Workers", "Restart background worker threads"],
        ]
        self.wizard.filename = "valid_checklist.xlsx"
        self.wizard.file_content = create_test_xlsx_base64(xlsx_rows)

        res = self.wizard.action_import_task_checklist_xlsx()
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('params', {}).get('type'), 'success')

        checklist = self.Checklist.search([('name', '=', unique_name)], limit=1)
        self.assertTrue(checklist)
        self.assertEqual(checklist.description, "Deployment Tasks")
        self.assertEqual(len(checklist.checklist_ids), 2)

    def test_action_import_task_checklist_csv(self):
        """Test action_import_task_checklist_csv with valid and invalid files."""
        # 1. Invalid file extension
        self.wizard.filename = "wrong_extension.xlsx"
        with self.assertRaises(UserError) as cm:
            self.wizard.action_import_task_checklist_csv()
        self.assertIn("Invalid file format", str(cm.exception))

        # 2. Empty file content
        self.wizard.filename = "valid_empty.csv"
        self.wizard.file_content = False
        with self.assertRaises(UserError) as cm:
            self.wizard.action_import_task_checklist_csv()
        self.assertIn("The uploaded file is empty or missing content", str(cm.exception))

        # 3. Valid CSV import
        unique_name = "CSV Code Review Checklist"
        csv_text = (
            "Checklist Name,Description,Checklist Item,Item Description\n"
            f"{unique_name},Code Review Process,Check Tests,Ensure all unit tests pass\n"
            f"{unique_name},Code Review Process,Check Lint,Ensure flake8 linter passes\n"
        )
        self.wizard.filename = "valid_checklist.csv"
        self.wizard.file_content = base64.b64encode(csv_text.encode('utf-8')).decode('utf-8')

        res = self.wizard.action_import_task_checklist_csv()
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('params', {}).get('type'), 'success')

        checklist = self.Checklist.search([('name', '=', unique_name)], limit=1)
        self.assertTrue(checklist)
        self.assertEqual(checklist.description, "Code Review Process")
        self.assertEqual(len(checklist.checklist_ids), 2)
