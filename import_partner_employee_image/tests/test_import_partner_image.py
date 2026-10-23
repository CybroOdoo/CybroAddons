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
class TestImportPartnerImage(TransactionCase):
    """Test cases for the partner image import wizard (import.partner.image)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.ImportPartnerWizard = cls.env['import.partner.image']

        cls.partner = cls.Partner.create({
            'name': 'Test Partner Corporation',
            'email': 'partner@test.com',
        })

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
        wizard = self.ImportPartnerWizard.new()
        self.assertEqual(wizard._clean_id('25'), '25')
        self.assertEqual(wizard._clean_id('25.0'), '25')
        self.assertEqual(wizard._clean_id(30.0), '30')
        self.assertEqual(wizard._clean_id(''), '')
        self.assertEqual(wizard._clean_id(None), '')

    def test_partner_import_csv_local_file(self):
        """Test importing partner image from local file path via CSV."""
        csv_content = "Employee/Partner Record ID,Image Link\n%s,%s\n" % (
            self.partner.id,
            self.temp_img.name,
        )
        wizard = self.ImportPartnerWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'partners.csv',
            'file_type': 'csv',
        })
        wizard.action_import_file()
        self.assertTrue(self.partner.image_1920, "Partner image should be updated from local file.")

    @patch('urllib3.PoolManager.request')
    def test_partner_import_csv_url(self, mock_request):
        """Test importing partner image from URL via CSV."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.data = SAMPLE_PNG_BYTES
        mock_request.return_value = mock_response

        self.partner.image_1920 = False

        csv_content = "Employee/Partner Record ID,Image Link\n%s,https://example.com/logo.png\n" % self.partner.id
        wizard = self.ImportPartnerWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'partners.csv',
            'file_type': 'csv',
        })
        wizard.action_import_file()
        self.assertTrue(self.partner.image_1920, "Partner image should be updated from URL.")

    def test_partner_import_excel(self):
        """Test importing partner image via Excel (.xlsx)."""
        self.partner.image_1920 = False
        rows = [
            ["Employee/Partner Record ID", "Image Link"],
            [self.partner.id, self.temp_img.name],
        ]
        excel_str = self._create_excel_file_str(rows)

        wizard = self.ImportPartnerWizard.create({
            'file': excel_str,
            'filename': 'partners.xlsx',
            'file_type': 'excel',
        })
        wizard.action_import_file()
        self.assertTrue(self.partner.image_1920, "Partner image should be updated from Excel.")

    def test_partner_missing_file(self):
        """Test error when no file is provided."""
        wizard = self.ImportPartnerWizard.new({'file_type': 'csv'})
        with self.assertRaises(UserError):
            wizard.action_import_file()

    def test_partner_file_type_mismatch_csv(self):
        """Test uploading Excel file when file_type is set to CSV."""
        excel_str = self._create_excel_file_str([["Record ID", "Image"]])
        wizard = self.ImportPartnerWizard.create({
            'file': excel_str,
            'filename': 'test.xlsx',
            'file_type': 'csv',
        })
        with self.assertRaises(ValidationError):
            wizard.action_import_file()

    def test_partner_file_type_mismatch_excel(self):
        """Test uploading CSV content when file_type is set to Excel."""
        csv_content = "ID,Image\n1,/tmp/test.png\n"
        wizard = self.ImportPartnerWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'test.csv',
            'file_type': 'excel',
        })
        with self.assertRaises(ValidationError):
            wizard.action_import_file()

    def test_partner_non_existent_id(self):
        """Test error when partner ID does not exist."""
        csv_content = "Employee/Partner Record ID,Image Link\n9999999,%s\n" % self.temp_img.name
        wizard = self.ImportPartnerWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'partners.csv',
            'file_type': 'csv',
        })
        with self.assertRaises(UserError):
            wizard.action_import_file()

    def test_partner_empty_fields(self):
        """Test error when partner ID or image field is empty."""
        csv_content = "Employee/Partner Record ID,Image Link\n,%s\n" % self.temp_img.name
        wizard = self.ImportPartnerWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'partners.csv',
            'file_type': 'csv',
        })
        with self.assertRaises(UserError):
            wizard.action_import_file()

    @patch('urllib3.PoolManager.request')
    def test_partner_url_not_found(self, mock_request):
        """Test error when URL returns HTTP 404."""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.data = b''
        mock_request.return_value = mock_response

        csv_content = "Employee/Partner Record ID,Image Link\n%s,https://example.com/missing.png\n" % self.partner.id
        wizard = self.ImportPartnerWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'partners.csv',
            'file_type': 'csv',
        })
        with self.assertRaises(UserError):
            wizard.action_import_file()

    def test_partner_invalid_local_path(self):
        """Test error when local file path does not exist."""
        csv_content = "Employee/Partner Record ID,Image Link\n%s,/non/existent/partner.png\n" % self.partner.id
        wizard = self.ImportPartnerWizard.create({
            'file': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'filename': 'partners.csv',
            'file_type': 'csv',
        })
        with self.assertRaises(UserError):
            wizard.action_import_file()
