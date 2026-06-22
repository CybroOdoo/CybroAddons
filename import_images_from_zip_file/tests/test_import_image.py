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
import io
import zipfile
from odoo.tests import common

class TestImportImage(common.TransactionCase):

    def setUp(self):
        super(TestImportImage, self).setUp()
        self.product = self.env['product.template'].create({
            'name': 'Test Product',
            'default_code': 'TP001',
        })
        self.image_content = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr('TP001.png', self.image_content)
        self.zip_file_base64 = base64.b64encode(zip_buffer.getvalue())

    def test_import_image_product_template(self):
        """Test importing product image based on internal reference"""
        wizard = self.env['import.image'].create({
            'file': self.zip_file_base64,
            'model_template': 'product.template',
            'product_product_selection': 'internal_reference',
        })
        self.assertFalse(self.product.image_1920)
        wizard.action_import()
        self.product.invalidate_recordset()
        self.assertTrue(self.product.image_1920)

    def test_import_image_partner(self):
        """Test importing partner image based on name"""
        partner = self.env['res.partner'].create({'name': 'Test Partner'})
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr('Test Partner.png', self.image_content)
        zip_file_base64 = base64.b64encode(zip_buffer.getvalue())
        wizard = self.env['import.image'].create({
            'file': zip_file_base64,
            'model_template': 'res.partner',
            'res_partner_selection': 'name',
        })
        self.assertFalse(partner.image_1920)
        wizard.action_import()
        partner.invalidate_recordset()
        self.assertTrue(partner.image_1920)
