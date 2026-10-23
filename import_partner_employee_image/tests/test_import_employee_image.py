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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64
import io
import os
import tempfile
from unittest.mock import MagicMock, patch

import openpyxl

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

# Sample 1x1 transparent PNG image in base64
SAMPLE_PNG_B64_STR = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
SAMPLE_PNG_BYTES = base64.b64decode(SAMPLE_PNG_B64_STR)


@tagged('post_install', '-at_install')
class TestImportEmployeeImage(TransactionCase):
    """Test cases for the employee image import wizard (import.employee.image)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Employee = cls.env['hr.employee']
        cls.ImportEmployeeWizard = cls.env['import.employee.image']

        cls.employee = cls.Employee.create({
            'name': 'Test John Doe',
        })

        # Create a temporary local image file for testing local file imports
        cls.temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        cls.temp_img.write(SAMPLE_PNG_BYTES)
        cls.temp_img.close()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_img.name):
            os.unlink(cls.temp_img.name)
        super().tearDownClass()

    def _create_excel_file_str(self, rows):
        """Helper to create an in-memory .xlsx file and return its base64 string."""
        wb = openpyxl.Workbook()
        ws = wb.active
        for row in rows:
            ws.append(row)
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return base64.b64encode(stream.getvalue()).decode('utf-8')

    def test_clean_id(self):
        """Test the _clean_id helper method for various numeric formats."""
        wizard = self.ImportEmployeeWizard.new()
        self.assertEqual(wizard._clean_id('12'), '12')
        self.assertEqual(wizard._clean_id('12.0'), '12')
        self.assertEqual(wizard._clean_id(15.0), '15')
        self.assertEqual(wizard._clean_id(''), '')
        self.assertEqual(wizard._clean_id(None), '')

    def test_employee_import_csv_local_file(self):
        """Test importing employee image from local file path via CSV."""
        csv_content = "Employee/Partner Record ID,Image Link\n%s,%s\n" % (
            self.employee.id,
            self.temp_img.name,
        )
        wizard = self.ImportEmployeeWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'employees.csv',
            'file_type': 'csv',
        })
        wizard.action_import_file()
        self.assertTrue(self.employee.image_1920, "Employee image should be updated from local file.")

    @patch('urllib3.PoolManager.request')
    def test_employee_import_csv_url(self, mock_request):
        """Test importing employee image from URL via CSV."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.data = SAMPLE_PNG_BYTES
        mock_request.return_value = mock_response

        self.employee.image_1920 = False

        csv_content = "Employee/Partner Record ID,Image Link\n%s,https://example.com/test.png\n" % self.employee.id
        wizard = self.ImportEmployeeWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'employees.csv',
            'file_type': 'csv',
        })
        wizard.action_import_file()
        self.assertTrue(self.employee.image_1920, "Employee image should be updated from URL.")

    def test_employee_import_excel(self):
        """Test importing employee image via Excel (.xlsx)."""
        self.employee.image_1920 = False
        rows = [
            ["Employee/Partner Record ID", "Image Link"],
            [self.employee.id, self.temp_img.name],
        ]
        excel_str = self._create_excel_file_str(rows)

        wizard = self.ImportEmployeeWizard.create({
            'file': excel_str,
            'filename': 'employees.xlsx',
            'file_type': 'excel',
        })
        wizard.action_import_file()
        self.assertTrue(self.employee.image_1920, "Employee image should be updated from Excel.")

    def test_employee_missing_file(self):
        """Test error when no file is provided."""
        wizard = self.ImportEmployeeWizard.new({'file_type': 'csv'})
        with self.assertRaises(UserError):
            wizard.action_import_file()

    def test_employee_file_type_mismatch_csv(self):
        """Test uploading Excel file when file_type is set to CSV."""
        excel_str = self._create_excel_file_str([["Record ID", "Image"]])
        wizard = self.ImportEmployeeWizard.create({
            'file': excel_str,
            'filename': 'test.xlsx',
            'file_type': 'csv',
        })
        with self.assertRaises(ValidationError):
            wizard.action_import_file()

    def test_employee_file_type_mismatch_excel(self):
        """Test uploading CSV content when file_type is set to Excel."""
        csv_content = "ID,Image\n1,/tmp/test.png\n"
        wizard = self.ImportEmployeeWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'test.csv',
            'file_type': 'excel',
        })
        with self.assertRaises(ValidationError):
            wizard.action_import_file()

    def test_employee_non_existent_id(self):
        """Test error when employee ID does not exist."""
        csv_content = "Employee/Partner Record ID,Image Link\n9999999,%s\n" % self.temp_img.name
        wizard = self.ImportEmployeeWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'employees.csv',
            'file_type': 'csv',
        })
        with self.assertRaises(UserError):
            wizard.action_import_file()

    def test_employee_empty_fields(self):
        """Test error when ID or image field is empty."""
        csv_content = "Employee/Partner Record ID,Image Link\n,%s\n" % self.temp_img.name
        wizard = self.ImportEmployeeWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'employees.csv',
            'file_type': 'csv',
        })
        with self.assertRaises(UserError):
            wizard.action_import_file()

    @patch('urllib3.PoolManager.request')
    def test_employee_url_not_found(self, mock_request):
        """Test error when URL returns HTTP 404."""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.data = b''
        mock_request.return_value = mock_response

        csv_content = "Employee/Partner Record ID,Image Link\n%s,https://example.com/notfound.png\n" % self.employee.id
        wizard = self.ImportEmployeeWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'employees.csv',
            'file_type': 'csv',
        })
        with self.assertRaises(UserError):
            wizard.action_import_file()

    def test_employee_invalid_local_path(self):
        """Test error when local file path does not exist."""
        csv_content = "Employee/Partner Record ID,Image Link\n%s,/non/existent/path/img.png\n" % self.employee.id
        wizard = self.ImportEmployeeWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'employees.csv',
            'file_type': 'csv',
        })
        with self.assertRaises(UserError):
            wizard.action_import_file()
