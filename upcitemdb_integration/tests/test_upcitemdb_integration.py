# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP (Contact : odoo@cybrosys.com)
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
#############################################################################
from unittest.mock import Mock, patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestUPCItemDBIntegration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.category = cls.env['product.category'].create({
            'name': 'Test Category'
        })

    def _mock_upc_response(self):
        """Return a valid UPCItemDB response."""
        response = Mock()
        response.json.return_value = {
            "code": "OK",
            "items": [{
                "title": "Test Product",
                "description": "Sample Product Description",
                "highest_recorded_price": 99.99,
                "model": "MODEL001",
                "category": "Electronics>Mobile",
                "weight": "2 kg",
                "images": []
            }]
        }
        return response

    def test_01_barcode_populates_product_details(self):
        """Valid UPC should populate product fields."""
        product = self.env['product.template'].new({
            'barcode': '123456789012'
        })

        with patch(
                'odoo.addons.upcitemdb_integration.models.'
                'product_template.requests.get',
                return_value=self._mock_upc_response()):
            product._onchange_barcode()

        self.assertEqual(product.name, "Test Product")
        self.assertEqual(
            product.description_sale,
            "Sample Product Description"
        )
        self.assertEqual(product.default_code, "MODEL001")
        self.assertEqual(product.list_price, 99.99)

    def test_02_duplicate_barcode_validation(self):
        """Duplicate barcode should raise ValidationError."""

        self.env['product.template'].create({
            'name': 'Existing Product',
            'barcode': '123456789012'
        })

        product = self.env['product.template'].new({
            'barcode': '123456789012'
        })

        with self.assertRaises(ValidationError):
            product._onchange_barcode()

    def test_03_invalid_upc_validation(self):
        """Invalid UPC should raise ValidationError."""

        response = Mock()
        response.json.return_value = {
            "code": "INVALID"
        }

        product = self.env['product.template'].new({
            'barcode': '123456789012'
        })

        with patch(
                'odoo.addons.upcitemdb_integration.models.'
                'product_template.requests.get',
                return_value=response):
            with self.assertRaises(ValidationError):
                product._onchange_barcode()

    def test_04_category_creation(self):
        """Missing category should be created automatically."""

        response = Mock()
        response.json.return_value = {
            "code": "OK",
            "items": [{
                "title": "Product",
                "description": "Description",
                "highest_recorded_price": 20,
                "model": "TEST",
                "category": "Electronics>Mobile",
                "weight": "1 kg",
                "images": []
            }]
        }

        product = self.env['product.template'].new({
            'barcode': '987654321012'
        })

        with patch(
                'odoo.addons.upcitemdb_integration.models.'
                'product_template.requests.get',
                return_value=response):
            product._onchange_barcode()

        self.assertTrue(product.categ_id)

    def test_05_weight_conversion_kg(self):
        """Weight should be converted correctly."""

        product = self.env['product.template'].new({
            'barcode': '123456789013'
        })

        with patch(
                'odoo.addons.upcitemdb_integration.models.'
                'product_template.requests.get',
                return_value=self._mock_upc_response()):
            product._onchange_barcode()

        self.assertEqual(product.weight, 2.0)

    def test_06_invalid_weight_unit(self):
        """Invalid weight unit should raise ValidationError."""

        response = Mock()
        response.json.return_value = {
            "code": "OK",
            "items": [{
                "title": "Product",
                "description": "Description",
                "highest_recorded_price": 10,
                "model": "TEST",
                "category": "Electronics",
                "weight": "5 xyz",
                "images": []
            }]
        }

        product = self.env['product.template'].new({
            'barcode': '123456789014'
        })

        with patch(
                'odoo.addons.upcitemdb_integration.models.'
                'product_template.requests.get',
                return_value=response):
            with self.assertRaises(ValidationError):
                product._onchange_barcode()

    def test_07_short_barcode_no_action(self):
        """Barcode shorter than 12 digits should do nothing."""

        product = self.env['product.template'].new({
            'barcode': '12345'
        })

        product._onchange_barcode()

        self.assertFalse(product.name)

    def test_08_13_digit_barcode_supported(self):
        """13 digit UPC should be accepted."""

        product = self.env['product.template'].new({
            'barcode': '1234567890123'
        })

        with patch(
                'odoo.addons.upcitemdb_integration.models.'
                'product_template.requests.get',
                return_value=self._mock_upc_response()):
            product._onchange_barcode()

        self.assertEqual(product.name, "Test Product")