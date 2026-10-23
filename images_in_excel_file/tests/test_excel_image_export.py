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
from unittest.mock import MagicMock, patch

from PIL import Image

import odoo.addons.images_in_excel_file.controllers.export as image_export
import odoo.addons.web.controllers.export as core_export
from odoo.addons.images_in_excel_file.controllers.export import (
    ExcelExportImage,
    ImageExportXlsxWriter,
    _decode_image_data,
    _is_candidate_image_field,
    _is_valid_image,
    _to_png_stream,
)
from odoo.addons.web.controllers.export import ExportXlsxWriter
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'images_in_excel_file')
class TestExcelImageExport(TransactionCase):
    """Test suite for image embedding in XLSX exports and controller behavior."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a small valid test PNG image in base64 format
        img = Image.new('RGB', (20, 20), color='blue')
        stream = io.BytesIO()
        img.save(stream, format='PNG')
        cls.raw_png = stream.getvalue()
        cls.b64_png = base64.b64encode(cls.raw_png).decode('ascii')

    def setUp(self):
        super().setUp()
        self.mock_request = MagicMock()
        self.mock_request.env = self.env

    def test_01_candidate_image_field_detection(self):
        """Verify field name and type detection for image fields."""
        # Standard image fields
        self.assertTrue(_is_candidate_image_field('image_1920'))
        self.assertTrue(_is_candidate_image_field('image_128'))
        self.assertTrue(_is_candidate_image_field('image'))

        # Avatar, photo, signature, logo fields
        self.assertTrue(_is_candidate_image_field('avatar_128'))
        self.assertTrue(_is_candidate_image_field('photo'))
        self.assertTrue(_is_candidate_image_field('signature'))
        self.assertTrue(_is_candidate_image_field('company_logo'))
        self.assertTrue(_is_candidate_image_field('partner_id/avatar_256'))

        # Binary/image field types
        self.assertTrue(_is_candidate_image_field('custom_field', field_type='binary'))
        self.assertTrue(_is_candidate_image_field('custom_field', field_type='image'))

        # Non-image fields
        self.assertFalse(_is_candidate_image_field('name'))
        self.assertFalse(_is_candidate_image_field('list_price'))
        self.assertFalse(_is_candidate_image_field('product_qty'))
        self.assertFalse(_is_candidate_image_field(''))

    def test_02_image_data_decoding_and_validation(self):
        """Verify decoding of raw bytes, base64 strings, and validation."""
        # Raw bytes
        decoded = _decode_image_data(self.raw_png)
        self.assertEqual(decoded, self.raw_png)
        self.assertTrue(_is_valid_image(decoded))

        # Base64 string
        decoded_b64 = _decode_image_data(self.b64_png)
        self.assertEqual(decoded_b64, self.raw_png)
        self.assertTrue(_is_valid_image(decoded_b64))

        # Data URI string
        data_uri = f'data:image/png;base64,{self.b64_png}'
        decoded_uri = _decode_image_data(data_uri)
        self.assertEqual(decoded_uri, self.raw_png)

        # Invalid or non-image content
        self.assertIsNone(_decode_image_data('not_base64_!@#$'))
        self.assertFalse(_is_valid_image(b'regular text content'))
        self.assertFalse(_is_valid_image(b''))

    def test_03_png_stream_conversion(self):
        """Verify conversion to PNG BytesIO stream and scaling calculation."""
        out_stream, x_scale, y_scale = _to_png_stream(self.raw_png)
        self.assertIsInstance(out_stream, io.BytesIO)
        self.assertGreater(len(out_stream.getvalue()), 0)
        self.assertGreater(x_scale, 0)
        self.assertGreater(y_scale, 0)

    def test_04_image_export_xlsx_writer_output(self):
        """Verify that ImageExportXlsxWriter writes valid XLSX with embedded images."""
        fields = [
            {'name': 'name', 'label': 'Product Name', 'type': 'char'},
            {'name': 'image_1920', 'label': 'Product Image', 'type': 'binary'},
            {'name': 'avatar_128', 'label': 'Avatar', 'type': 'binary'},
        ]
        headers = ['Product Name', 'Product Image', 'Avatar']
        rows = [
            ['Test Product A', self.b64_png, self.b64_png],
            ['Test Product B', False, ''],
        ]

        with patch.object(core_export, 'request', self.mock_request):
            with ImageExportXlsxWriter(fields, headers, len(rows)) as writer:
                for row_idx, row in enumerate(rows):
                    for col_idx, val in enumerate(row):
                        writer.write_cell(row_idx + 1, col_idx, val)

            xlsx_data = writer.value
            self.assertTrue(bool(xlsx_data))
            self.assertIsInstance(xlsx_data, bytes)
            # XLSX files start with ZIP magic bytes 'PK\x03\x04'
            self.assertTrue(xlsx_data.startswith(b'PK\x03\x04'))

    def test_05_controller_from_data(self):
        """Verify ExcelExportImage controller from_data produces valid XLSX data."""
        controller = ExcelExportImage()
        fields = [
            {'name': 'name', 'label': 'Name', 'type': 'char'},
            {'name': 'image_1920', 'label': 'Image', 'type': 'binary'},
        ]
        headers = ['Name', 'Image']
        rows = [
            ['Product 1', self.b64_png],
            ['Product 2', None],
        ]

        with patch.object(core_export, 'request', self.mock_request):
            with patch.object(image_export, 'request', self.mock_request):
                result = controller.from_data(fields, headers, rows)
                self.assertTrue(bool(result))
                self.assertIsInstance(result, bytes)
                self.assertTrue(result.startswith(b'PK\x03\x04'))

    def test_06_core_export_writer_not_monkey_patched(self):
        """Ensure core ExportXlsxWriter remains pristine and is not monkey-patched."""
        # ExportXlsxWriter methods must not have been overwritten globally
        self.assertFalse(hasattr(ExportXlsxWriter, '_img_field_names'))
        self.assertNotEqual(ExportXlsxWriter.write_cell, ImageExportXlsxWriter.write_cell)
