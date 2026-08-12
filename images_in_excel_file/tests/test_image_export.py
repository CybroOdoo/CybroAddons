# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
from odoo.tests.common import TransactionCase
from odoo.addons.web.controllers.export import ExportXlsxWriter

class TestImageExport(TransactionCase):

    def setUp(self):
        super(TestImageExport, self).setUp()
        # Create a tiny valid PNG image
        self.image_base64 = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        self.image_raw = base64.b64decode(self.image_base64)

    def test_is_image_field(self):
        from odoo.addons.images_in_excel_file.controllers.export import _is_image_field
        self.assertTrue(_is_image_field('image_1920'))
        self.assertTrue(_is_image_field('product_logo'))
        self.assertTrue(_is_image_field('partner_picture'))
        self.assertFalse(_is_image_field('name'))
        self.assertFalse(_is_image_field('document_file'))

    def test_binary_convert_to_export(self):
        from odoo.fields import Binary
        # Create a mock Binary field class to avoid testing actual database operations
        class MockBinaryField:
            name = 'image_1920'
        
        field = MockBinaryField()
        # If value is bytes (from our base64 test image), it should return bytes
        res = Binary.convert_to_export(field, self.image_base64, None)
        self.assertEqual(res, self.image_base64)

    def test_xlsx_writer_patch(self):
        fields = [{'name': 'image_1920', 'label': 'Image'}, {'name': 'name', 'label': 'Name'}]
        columns_headers = ['Image', 'Name']
        
        writer = ExportXlsxWriter(fields, columns_headers, row_count=1)
        self.assertTrue(hasattr(writer, '_img_field_names'))
        self.assertTrue(hasattr(writer, '_img_row_heights_set'))
        self.assertEqual(writer._img_field_names, ['image_1920', 'name'])
        
        # Test write_cell with image Data URI
        data_uri = b'data:image/png;base64,' + self.image_base64
        writer.write_cell(1, 0, data_uri)
        
        # Check that the row/col sizes were modified
        self.assertIn(1, writer._img_row_heights_set)
        self.assertIn(0, writer._img_col_widths_set)
        
        # Test write_cell with non-image simple value
        writer.write_cell(1, 1, 'Test Name')
