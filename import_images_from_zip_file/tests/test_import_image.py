# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K @cybrosys(odoo@cybrosys.com)
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
###############################################################################
import base64
import io
import zipfile

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestImportImage(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Product Template',
        })
        cls.product_product = cls.env['product.product'].create({
            'name': 'Test Product Variant',
            'default_code': 'TEST001',
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'identification_id': 'EMP001',
        })

    def _create_zip_file(self, filename):
        """Create valid in-memory zip image"""
        # Valid 1x1 PNG image
        image_base64 = (
            b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='
        )
        image_content = base64.b64decode(image_base64)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
                zip_buffer,
                'w',
                zipfile.ZIP_DEFLATED
        ) as zip_file:
            zip_file.writestr(
                filename,
                image_content
            )
        zip_buffer.seek(0)
        return base64.b64encode(
            zip_buffer.read()
        )

    def test_partner_action_open_wizard(self):
        """Test partner wizard action"""
        action = self.partner.action_open_import_image_wizard()
        self.assertEqual(
            action['res_model'],
            'import.image'
        )
        self.assertEqual(
            action['target'],
            'new'
        )

    def test_product_template_action_open_wizard(self):
        """Test product.template wizard action"""
        action = (
            self.product_template
            .action_open_import_image_wizard()
        )
        self.assertEqual(
            action['res_model'],
            'import.image'
        )

    def test_product_product_action_open_wizard(self):
        """Test product.product wizard action"""
        action = (
            self.product_product
            .action_open_import_image_wizard()
        )
        self.assertEqual(
            action['res_model'],
            'import.image'
        )

    def test_employee_action_open_wizard(self):
        """Test employee wizard action"""
        action = (
            self.employee
            .action_open_import_image_wizard()
        )
        self.assertEqual(
            action['res_model'],
            'import.image'
        )

    def test_import_without_file(self):
        """Test validation without file"""
        wizard = self.env['import.image'].create({
            'model_template': 'res.partner',
        })
        with self.assertRaises(ValidationError):
            wizard.action_import()

    def test_invalid_zip_file(self):
        """Test invalid zip file"""
        wizard = self.env['import.image'].create({
            'model_template': 'res.partner',
            'file': base64.b64encode(
                b'invalid zip content'
            ),
        })
        with self.assertRaises(ValidationError):
            wizard.action_import()

    def test_partner_image_import(self):
        """Test partner image import"""
        zip_file = self._create_zip_file(
            'Test Partner.png'
        )
        wizard = self.env['import.image'].create({
            'model_template': 'res.partner',
            'file': zip_file,
            'res_partner_selection': 'name',
        })
        result = wizard.action_import()
        self.partner.invalidate_recordset(
            ['image_1920']
        )
        self.assertTrue(
            self.partner.image_1920
        )
        self.assertEqual(
            result['tag'],
            'reload'
        )

    def test_product_template_image_import(self):
        """Test product template image import"""
        zip_file = self._create_zip_file(
            'Test Product Template.png'
        )
        wizard = self.env['import.image'].create({
            'model_template': 'product.template',
            'file': zip_file,
            'product_template_selection': 'name',
        })
        wizard.action_import()
        self.product_template.invalidate_recordset(
            ['image_1920']
        )
        self.assertTrue(
            self.product_template.image_1920
        )

    def test_product_product_import_by_reference(self):
        """Test import using internal reference"""
        zip_file = self._create_zip_file(
            'TEST001.png'
        )
        wizard = self.env['import.image'].create({
            'model_template': 'product.product',
            'file': zip_file,
            'product_product_selection':
                'internal_reference',
        })
        wizard.action_import()
        self.product_product.invalidate_recordset(
            ['image_1920']
        )
        self.assertTrue(
            self.product_product.image_1920
        )

    def test_employee_image_import(self):
        """Test employee image import"""

        zip_file = self._create_zip_file(
            'Test Employee.png'
        )
        wizard = self.env['import.image'].create({
            'model_template': 'hr.employee',
            'file': zip_file,
            'hr_employee_selection': 'name',
        })
        wizard.action_import()
        self.employee.invalidate_recordset(
            ['image_1920']
        )
        self.assertTrue(
            self.employee.image_1920
        )
