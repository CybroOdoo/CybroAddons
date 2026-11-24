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
#    This program is distributed in the hope it will be useful,
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
from io import BytesIO

from openpyxl import Workbook

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestImportTaskChecklist(TransactionCase):
    """Test suite for single-row task checklist and items import."""

    def setUp(self):
        super().setUp()
        self.ImportWizard = self.env['import.task.checklist']
        self.Checklist = self.env['task.checklist']
        self.ChecklistItem = self.env['checklist.item']
        self.company = self.env.company

    def test_import_csv_horizontal_items(self):
        """Test importing checklists with items in a single row from CSV."""
        csv_data = [
            ['Name', 'Description', 'Company', 'Checklist 1', 'Checklist 2', 'Checklist 3'],
            ['Deployment', 'Deploy steps', self.company.name, 'Run tests', 'Tag release', 'Deploy app'],
            ['Onboarding', 'New hire steps', self.company.name, 'Setup email', 'Assign laptop'],
        ]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)
        csv_content = base64.b64encode(output.getvalue().encode('utf-8'))

        wizard = self.ImportWizard.create({
            'file_type': 'csv',
            'file_content': csv_content,
            'filename': 'test.csv',
        })
        wizard.action_import_task_checklist_csv()

        deploy = self.Checklist.search([('name', '=', 'Deployment'), ('company_id', '=', self.company.id)])
        self.assertTrue(deploy, "Deployment checklist should be created")
        self.assertEqual(deploy.description, 'Deploy steps')
        self.assertEqual(len(deploy.checklist_ids), 3, "Deployment should have 3 checklist items")

        item1 = deploy.checklist_ids.filtered(lambda i: i.name == 'Run tests')
        self.assertTrue(item1)
        self.assertEqual(item1.sequence, 1)

        item2 = deploy.checklist_ids.filtered(lambda i: i.name == 'Tag release')
        self.assertTrue(item2)
        self.assertEqual(item2.sequence, 2)

        item3 = deploy.checklist_ids.filtered(lambda i: i.name == 'Deploy app')
        self.assertTrue(item3)
        self.assertEqual(item3.sequence, 3)

        onboarding = self.Checklist.search([('name', '=', 'Onboarding'), ('company_id', '=', self.company.id)])
        self.assertTrue(onboarding, "Onboarding checklist should be created")
        self.assertEqual(len(onboarding.checklist_ids), 2)

    def test_import_csv_empty(self):
        """Test that importing without a file raises a UserError."""
        wizard = self.ImportWizard.create({
            'file_type': 'csv',
            'file_content': False,
            'filename': 'test.csv',
        })
        with self.assertRaises(UserError):
            wizard.action_import_task_checklist_csv()

    def test_import_csv_invalid_format(self):
        """Test that importing invalid CSV content raises a UserError."""
        invalid_content = base64.b64encode(b'')
        wizard = self.ImportWizard.create({
            'file_type': 'csv',
            'file_content': invalid_content,
            'filename': 'test.csv'
        })

        with self.assertRaises(UserError):
            wizard.action_import_task_checklist_csv()

    def test_import_csv_no_records(self):
        """Test importing a CSV containing only headers creates no records."""
        csv_data = [['Name', 'Description', 'Company', 'Checklist 1']]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(csv_data)
        csv_content = base64.b64encode(output.getvalue().encode('utf-8'))

        wizard = self.ImportWizard.create({
            'file_type': 'csv',
            'file_content': csv_content,
            'filename': 'test.csv'
        })

        count_before = self.Checklist.search_count([
            ('company_id', '=', self.company.id)
        ])

        wizard.action_import_task_checklist_csv()

        count_after = self.Checklist.search_count([
            ('company_id', '=', self.company.id)
        ])

        self.assertEqual(
            count_before,
            count_after,
            "No tasks should be created from a header-only CSV"
        )

    def test_import_xlsx_horizontal_items(self):
        """Test importing checklists with items in a single row from XLSX format."""
        wb = Workbook()
        ws = wb.active
        ws.append(['Name', 'Description', 'Company', 'Checklist 1', 'Checklist 2'])
        ws.append(['XLSX Checklist', 'XLSX Desc', self.company.name, 'Step A', 'Step B'])
        output = BytesIO()
        wb.save(output)

        xlsx_content = base64.b64encode(output.getvalue())
        wizard = self.ImportWizard.create({
            'file_type': 'xls',
            'file_content': xlsx_content,
            'filename': 'test.xlsx',
        })
        wizard.action_import_task_checklist_xlsx()

        task3 = self.Checklist.search([('name', '=', 'XLSX Checklist'), ('company_id', '=', self.company.id)])
        self.assertTrue(task3, "Checklist should be created from XLSX")
        self.assertEqual(task3.description, 'XLSX Desc')
        self.assertEqual(len(task3.checklist_ids), 2)
        self.assertEqual(task3.checklist_ids[0].name, 'Step A')
        self.assertEqual(task3.checklist_ids[0].sequence, 1)
        self.assertEqual(task3.checklist_ids[1].name, 'Step B')
        self.assertEqual(task3.checklist_ids[1].sequence, 2)

    def test_import_xlsx_invalid(self):
        """Test that importing non-XLSX bytes raises a UserError."""
        invalid_content = base64.b64encode(b'invalid xlsx data')
        wizard = self.ImportWizard.create({
            'file_type': 'xls',
            'file_content': invalid_content,
            'filename': 'test.xlsx',
        })
        with self.assertRaises(UserError):
            wizard.action_import_task_checklist_xlsx()
