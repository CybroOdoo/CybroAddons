# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import io
import json
from zipfile import ZipFile

from odoo import http
from odoo.tests.common import HttpCase, TransactionCase, tagged

from odoo.addons.export_x2many.controllers.export_x2many import (
    MultiSheetExcelExport,
    MultiSheetExportXlsxWriter,
)

XLSX_MIME = (
    'application/vnd.openxmlformats-officedocument'
    '.spreadsheetml.sheet'
)


@tagged('post_install', '-at_install')
class TestMultiSheetExportController(HttpCase):
    """Integration tests for MultiSheetExcelExport controller."""

    @classmethod
    def setUpClass(cls):
        """Set up test records for multisheet export tests."""
        super().setUpClass()
        cls.company_partner = cls.env['res.partner'].create({
            'name': 'Test Company Corp',
            'is_company': True,
            'email': 'company@test.com',
        })
        cls.individual_partner = cls.env['res.partner'].create({
            'name': 'Test Individual Person',
            'is_company': False,
            'email': 'individual@test.com',
        })

    def test_multisheet_xlsx_export(self):
        """Verify multisheet XLSX download with domain-filtered sheets."""
        self.authenticate('admin', 'admin')
        payload = {
            'model': 'res.partner',
            'fields': [
                {'name': 'name', 'label': 'Name', 'type': 'char'},
                {'name': 'email', 'label': 'Email', 'type': 'char'},
            ],
            'ids': [self.company_partner.id, self.individual_partner.id],
            'domain': [],
            'import_compat': False,
            'context': {},
            'sheet_list': [
                {
                    'name': 'Companies',
                    'domain': "[('is_company', '=', True)]",
                },
                {
                    'name': 'Individuals',
                    'domain': "[('is_company', '=', False)]",
                },
            ],
        }

        response = self.url_open(
            '/web/export/xlsx_multisheet',
            data={
                'data': json.dumps(payload),
                'csrf_token': http.Request.csrf_token(self),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            XLSX_MIME,
            response.headers.get('Content-Type', ''),
        )

        zip_file = ZipFile(io.BytesIO(response.content))
        file_list = zip_file.namelist()
        self.assertIn('xl/worksheets/sheet1.xml', file_list)
        self.assertIn('xl/worksheets/sheet2.xml', file_list)

    def test_multisheet_xlsx_export_fallback(self):
        """Verify fallback to standard export when sheet_list is absent."""
        self.authenticate('admin', 'admin')
        payload = {
            'model': 'res.partner',
            'fields': [
                {'name': 'name', 'label': 'Name', 'type': 'char'},
                {'name': 'email', 'label': 'Email', 'type': 'char'},
            ],
            'ids': [self.company_partner.id],
            'domain': [],
            'import_compat': False,
            'context': {},
        }

        response = self.url_open(
            '/web/export/xlsx_multisheet',
            data={
                'data': json.dumps(payload),
                'csrf_token': http.Request.csrf_token(self),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            XLSX_MIME,
            response.headers.get('Content-Type', ''),
        )

        zip_file = ZipFile(io.BytesIO(response.content))
        self.assertIn('xl/worksheets/sheet1.xml', zip_file.namelist())


@tagged('post_install', '-at_install')
class TestMultiSheetExportWriter(TransactionCase):
    """Unit tests for MultiSheetExportXlsxWriter workbook construction."""

    def test_writer_multisheet_generation(self):
        """Test creating multiple sheets and writing headers and cells."""
        fields = [{'name': 'name', 'type': 'char'}]
        headers = ['Name']
        writer = MultiSheetExportXlsxWriter(fields, headers)

        # Add first sheet
        sheet1 = writer.workbook.add_worksheet('First Sheet')
        writer.set_worksheet(sheet1)
        writer.write_header()
        writer.write_cell(1, 0, 'First Record')

        # Add second sheet
        sheet2 = writer.workbook.add_worksheet('Second Sheet')
        writer.set_worksheet(sheet2)
        writer.write_header()
        writer.write_cell(1, 0, 'Second Record')

        writer.close()
        self.assertTrue(writer.value)
        self.assertTrue(writer.value.startswith(b'PK'))

    def test_sheet_name_sanitization_and_uniqueness(self):
        """Sanitize prohibited characters, and generate unique names."""
        used = set()
        name1 = MultiSheetExcelExport._sanitize_sheet_name(
            "Sales [2026] / US:NY", used,
        )
        self.assertEqual(name1, "Sales _2026_ _ US_NY")
        self.assertIn(name1, used)

        name2 = MultiSheetExcelExport._sanitize_sheet_name(
            "Sales _2026_ _ US_NY", used,
        )
        self.assertEqual(name2, "Sales _2026_ _ US_NY_1")
        self.assertIn(name2, used)

        name3 = MultiSheetExcelExport._sanitize_sheet_name("", used)
        self.assertEqual(name3, "Sheet")
