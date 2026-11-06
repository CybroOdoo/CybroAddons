# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
# pylint: disable=protected-access,unused-argument
"""Test suite for upcitemdb_integration module."""
import base64
from unittest.mock import Mock, patch
import requests

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.upcitemdb_integration import pre_init_hook

PATCH_PATH = 'odoo.addons.upcitemdb_integration.models.product_template.requests.get'
# 1x1 transparent png
DUMMY_PNG_BYTES = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
)


@tagged('post_install', '-at_install')
class TestUpcitemdbIntegration(TransactionCase):
    """Test UPC item lookup, category hierarchy, weight, and image handling."""

    @classmethod
    def setUpClass(cls):
        """Set up base test data."""
        super().setUpClass()
        cls.product_model = cls.env['product.template']
        cls.test_barcode = '012345678905'

    def test_01_barcode_ignored_if_invalid_length(self):
        """Verify barcodes with length other than 12 or 13 do not trigger lookup."""
        product = self.product_model.new({'barcode': '123'})
        with patch(PATCH_PATH) as mock_get:
            product._onchange_barcode()
            mock_get.assert_not_called()

        product.barcode = False
        with patch(PATCH_PATH) as mock_get:
            product._onchange_barcode()
            mock_get.assert_not_called()

    def test_02_barcode_already_exists(self):
        """Verify error is raised if barcode already exists on another product."""
        self.product_model.create({
            'name': 'Existing Product',
            'barcode': self.test_barcode,
        })
        new_product = self.product_model.new({'barcode': self.test_barcode})
        with self.assertRaises(ValidationError):
            new_product._onchange_barcode()

    def test_03_upc_lookup_success_full(self):
        """Verify successful UPCitemdb lookup with full details."""
        api_data = {
            'code': 'OK',
            'items': [{
                'title': 'Test Wireless Headphones',
                'description': 'Noise cancelling bluetooth headphones',
                'highest_recorded_price': 149.99,
                'model': 'WH-1000XM4',
                'category': 'Electronics > Audio > Headphones',
                'weight': '0.5 kg',
                'images': ['https://example.com/test_headphone.png'],
            }],
        }
        mock_api_resp = Mock()
        mock_api_resp.status_code = 200
        mock_api_resp.json.return_value = api_data

        mock_img_resp = Mock()
        mock_img_resp.status_code = 200
        mock_img_resp.content = DUMMY_PNG_BYTES

        def mock_get(url, **kwargs):
            if 'lookup?upc=' in url:
                return mock_api_resp
            return mock_img_resp

        product = self.product_model.new({'barcode': '987654321012'})
        with patch(PATCH_PATH, side_effect=mock_get):
            product._onchange_barcode()

        self.assertEqual(product.name, 'Test Wireless Headphones')
        self.assertEqual(product.description_sale, 'Noise cancelling bluetooth headphones')
        self.assertEqual(product.list_price, 149.99)
        self.assertEqual(product.default_code, 'WH-1000XM4')
        self.assertEqual(product.categ_id.name, 'Headphones')
        self.assertEqual(product.categ_id.parent_id.name, 'Audio')
        self.assertEqual(product.weight, 0.5)
        self.assertTrue(product.image_1920)

    def test_04_upc_weight_in_lbs_and_units(self):
        """Verify weight conversions under metric and imperial configurations."""
        product = self.product_model.new({'barcode': '555555555555'})

        # Test weight in pounds when product.weight_in_lbs is '1'
        icp = self.env['ir.config_parameter'].sudo()
        if hasattr(icp, 'set_str'):
            icp.set_str('product.weight_in_lbs', '1')
        else:
            getattr(icp, 'set_param', lambda k, v: None)('product.weight_in_lbs', '1')

        product._set_upc_weight({'weight': '2.5 lbs'})
        self.assertAlmostEqual(product.weight, 2.5)

        # Test empty weight
        product._set_upc_weight({'weight': ''})
        self.assertEqual(product.weight, 0)

        # Test invalid weight unit
        with self.assertRaises(ValidationError):
            product._set_upc_weight({'weight': '10 unknown_unit'})

        # Reset parameter
        if hasattr(icp, 'set_str'):
            icp.set_str('product.weight_in_lbs', '0')
        else:
            getattr(icp, 'set_param', lambda k, v: None)('product.weight_in_lbs', '0')

    def test_05_upc_empty_and_existing_categories(self):
        """Verify category handling when empty or category already exists."""
        product = self.product_model.new({'barcode': '777777777777'})

        # Empty category assigns default category
        product._set_upc_category({'category': ''})
        self.assertTrue(product.categ_id)

        # Existing category is reused rather than duplicated
        categ = self.env['product.category'].create({'name': 'ExistingUniqueCategory'})
        product._set_upc_category({'category': 'ExistingUniqueCategory'})
        self.assertEqual(product.categ_id.id, categ.id)

    def test_06_upc_image_failure_handling(self):
        """Verify image fetching handles request exceptions gracefully."""
        product = self.product_model.new({'barcode': '888888888888'})
        with patch(PATCH_PATH, side_effect=requests.RequestException("Network error")):
            product._set_upc_image({'images': ['https://example.com/broken.png']})
        self.assertFalse(product.image_1920)

    def test_07_invalid_upc_response(self):
        """Verify invalid UPC response code raises ValidationError."""
        product = self.product_model.new({'barcode': '444444444444'})
        mock_resp = Mock()
        mock_resp.json.return_value = {'code': 'INVALID_UPC', 'items': []}
        with patch(PATCH_PATH, return_value=mock_resp):
            with self.assertRaises(ValidationError):
                product._onchange_barcode()

    def test_08_api_request_exception(self):
        """Verify API network failure raises ValidationError."""
        product = self.product_model.new({'barcode': '444444444445'})
        with patch(PATCH_PATH, side_effect=requests.RequestException("Connection error")):
            with self.assertRaises(ValidationError):
                product._onchange_barcode()

    def test_09_pre_init_hook(self):
        """Verify pre_init_hook activates inactive currencies."""
        currency = self.env['res.currency'].search([('active', '=', True)], limit=1)
        if currency:
            currency.write({'active': False})
            self.assertFalse(currency.active)
            pre_init_hook(self.env)
            self.assertTrue(currency.active)

    def test_10_access_rights(self):
        """Verify standard user can read products with UPC attributes."""
        user = self.env.ref('base.user_demo', raise_if_not_found=False)
        if not user:
            group_field = (
                'group_ids' if 'group_ids' in self.env['res.users']._fields else 'groups_id'
            )
            user = self.env['res.users'].create({
                'name': 'Test UPC User',
                'login': 'test_upc_user_demo',
                group_field: [(6, 0, [self.env.ref('base.group_user').id])],
            })
        product = self.product_model.create({
            'name': 'Admin Product Test',
            'barcode': '111111111112',
        })
        read_res = product.with_user(user).read(['name', 'barcode'])
        self.assertTrue(read_res)
        self.assertEqual(read_res[0]['name'], 'Admin Product Test')
