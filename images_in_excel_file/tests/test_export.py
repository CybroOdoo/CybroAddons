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

from odoo.addons.images_in_excel_file.controllers.export import _is_image_field, _to_png_stream
from odoo.tests import TransactionCase

class TestImageExport(TransactionCase):

    def test_is_image_field(self):
        """Test _is_image_field logic for various field names."""
        self.assertTrue(_is_image_field("image_128"))
        self.assertTrue(_is_image_field("company_logo"))
        self.assertTrue(_is_image_field("profile_picture"))
        self.assertTrue(_is_image_field("some_icon"))
        self.assertTrue(_is_image_field("res.partner/image_1920"))
        
        self.assertFalse(_is_image_field("name"))
        self.assertFalse(_is_image_field("description"))
        self.assertFalse(_is_image_field("binary_data"))

    def test_to_png_stream(self):
        """Test conversion of raw image bytes to a PNG stream."""
        # 1x1 pixel PNG
        small_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT\x08\xd7c\xf8'
            b'\xff\xff?\x00\x05\xfe\x02\xfe\xa74\x00\x19\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        stream, xs, ys = _to_png_stream(small_png)
        self.assertIsNotNone(stream)
        stream_content = stream.read()
        self.assertTrue(stream_content.startswith(b'\x89PNG'))
        self.assertGreater(xs, 0)
        self.assertGreater(ys, 0)

    def test_patch_applied(self):
        """Check if the monkey-patches were successfully applied."""
        from odoo.fields import Binary
        from odoo.addons.web.controllers.export import ExportXlsxWriter

        self.assertTrue(getattr(Binary, '_image_excel_export_patched', False))
        self.assertTrue(getattr(ExportXlsxWriter, '_image_excel_export_patched', False))
