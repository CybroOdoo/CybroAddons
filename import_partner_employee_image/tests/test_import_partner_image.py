# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bashir Muhammed A (odoo@cybrosys.com)
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
################################################################################
import base64
import io
import os
import openpyxl
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestImportPartnerImage(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        # Minimal valid 1x1 GIF image
        cls.dummy_image_data = base64.b64decode(
            b'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
        )

        # Temporary image file on disk for local file import test
        cls.temp_image_path = os.path.join(
            os.path.dirname(__file__), 'temp_test_partner_image.gif'
        )
        with open(cls.temp_image_path, 'wb') as f:
            f.write(cls.dummy_image_data)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_image_path):
            try:
                os.remove(cls.temp_image_path)
            except OSError:
                pass
        super().tearDownClass()

    def test_01_import_partner_image_csv_local(self):
        """Test importing partner image from CSV with a local file path"""
        csv_content = f"partner_id,partner_image\n{self.partner.id},{self.temp_image_path}\n"
        csv_binary = base64.b64encode(csv_content.encode('utf-8'))

        wizard = self.env['import.partner_image'].create({
            'file': csv_binary,
            'file_type': 'csv',
        })
        wizard.action_import_file()

        # Verify partner image was updated correctly
        self.assertTrue(self.partner.image_1920)
        self.assertEqual(base64.b64decode(self.partner.image_1920), self.dummy_image_data)

    def test_02_import_partner_image_excel_local(self):
        """Test importing partner image from Excel with a local file path"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['partner_id', 'partner_image'])
        ws.append([self.partner.id, self.temp_image_path])

        fp = io.BytesIO()
        wb.save(fp)
        excel_binary = base64.b64encode(fp.getvalue())

        wizard = self.env['import.partner_image'].create({
            'file': excel_binary,
            'file_type': 'excel',
        })
        wizard.action_import_file()

        # Verify partner image was updated correctly
        self.assertTrue(self.partner.image_1920)
        self.assertEqual(base64.b64decode(self.partner.image_1920), self.dummy_image_data)

    def test_03_import_partner_image_csv_url(self):
        """Test importing partner image from CSV with a URL"""
        csv_content = f"partner_id,partner_image\n{self.partner.id},https://example.com/test_partner_image.gif\n"
        csv_binary = base64.b64encode(csv_content.encode('utf-8'))

        wizard = self.env['import.partner_image'].create({
            'file': csv_binary,
            'file_type': 'csv',
        })

        class MockResponse:
            def __init__(self, data):
                self.data = data

        with patch('urllib3.PoolManager.request') as mock_request:
            mock_request.return_value = MockResponse(self.dummy_image_data)
            wizard.action_import_file()
            mock_request.assert_called_once_with('GET', 'https://example.com/test_partner_image.gif')

        # Verify partner image was updated correctly
        self.assertTrue(self.partner.image_1920)
        self.assertEqual(base64.b64decode(self.partner.image_1920), self.dummy_image_data)

    def test_04_import_partner_image_float_id(self):
        """Test importing partner image where the ID in the file is a float representation (e.g. from Excel)"""
        float_id_str = f"{self.partner.id}.0"
        csv_content = f"partner_id,partner_image\n{float_id_str},{self.temp_image_path}\n"
        csv_binary = base64.b64encode(csv_content.encode('utf-8'))

        wizard = self.env['import.partner_image'].create({
            'file': csv_binary,
            'file_type': 'csv',
        })
        wizard.action_import_file()

        self.assertTrue(self.partner.image_1920)

    def test_05_import_partner_image_validation_errors(self):
        """Test validation and user errors during partner image import"""
        # Case 1: Empty partner id
        csv_content_empty_id = f"partner_id,partner_image\n,{self.temp_image_path}\n"
        csv_binary_empty_id = base64.b64encode(csv_content_empty_id.encode('utf-8'))
        wizard_empty_id = self.env['import.partner_image'].create({
            'file': csv_binary_empty_id,
            'file_type': 'csv',
        })
        with self.assertRaises(UserError):
            wizard_empty_id.action_import_file()

        # Case 2: Empty image path
        csv_content_empty_img = f"partner_id,partner_image\n{self.partner.id},\n"
        csv_binary_empty_img = base64.b64encode(csv_content_empty_img.encode('utf-8'))
        wizard_empty_img = self.env['import.partner_image'].create({
            'file': csv_binary_empty_img,
            'file_type': 'csv',
        })
        with self.assertRaises(UserError):
            wizard_empty_img.action_import_file()

        # Case 3: Invalid file data (not UTF-8 decodable)
        invalid_data = base64.b64encode(b'\xff\xff\xff\xff')
        wizard_invalid = self.env['import.partner_image'].create({
            'file': invalid_data,
            'file_type': 'csv',
        })
        with self.assertRaises(ValidationError):
            wizard_invalid.action_import_file()
