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
import io

import openpyxl

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestSampleDownload(HttpCase):
    """Test the download of the sample Excel sheet."""

    def test_01_download_sample_sheet(self):
        """Verify a logged in user downloads a valid sample sheet."""
        self.authenticate('admin', 'admin')
        response = self.url_open('/download/excel')
        self.assertEqual(response.status_code, 200)
        self.assertIn('my_excel_file.xlsx',
                      response.headers['Content-Disposition'])
        sheet = openpyxl.load_workbook(io.BytesIO(response.content)).active
        rows = list(sheet.iter_rows(values_only=True))
        self.assertEqual(rows[0], ('Lots', 'Product', 'Quantity'))
        self.assertEqual(len(rows), 4)

    def test_02_download_requires_login(self):
        """Verify the sample sheet is not served to anonymous visitors."""
        response = self.url_open('/download/excel', allow_redirects=False)
        self.assertNotEqual(response.status_code, 200)
