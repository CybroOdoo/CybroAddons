# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import json
from unittest.mock import MagicMock, patch
from odoo.tests import common


class TestBarcodeSearch(common.HttpCase):
    """Test cases for checking the ecommerce barcode search functionality."""

    @classmethod
    def setUpClass(cls):
        super(TestBarcodeSearch, cls).setUpClass()
        # Create a dedicated test user
        cls.user_login = 'test_barcode_user'
        cls.user_password = 'test_password_123'
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Barcode User',
            'login': cls.user_login,
            'password': cls.user_password,
        })
        
        # Create a product with a barcode
        cls.product = cls.env['product.product'].create({
            'name': 'Barcode Test Product',
            'barcode': '1234567890123',
            'list_price': 50.0,
            'website_published': True,
        })

    def setUp(self):
        super(TestBarcodeSearch, self).setUp()
        # Authenticate for each test
        self.authenticate(self.user_login, self.user_password)

    def test_01_barcode_search_route(self):
        """Test the barcode search JSONRPC route."""
        # Scenario A: Valid Barcode
        payload = {'params': {'last_code': self.product.barcode}}
        response = self.url_open(
            '/shop/barcode/product',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content).get('result')
        
        self.assertTrue(result, "Should return a result for valid barcode")
        self.assertEqual(result.get('type'), 'ir.actions.act_url',
                         "Should return an act_url action")
        self.assertIn('extra_param=true', result.get('url'),
                      "The redirect URL should contain the extra_param")

        # Scenario B: Invalid Barcode
        payload = {'params': {'last_code': '0000000000000'}}
        response = self.url_open(
            '/shop/barcode/product',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        result = json.loads(response.content).get('result')
        self.assertFalse(result, "Should return False for an invalid barcode")

    def test_02_product_page_extra_param(self):
        """Test that the product page is reachable with the extra_param."""
        # Use slug to match real URL structure
        slug = self.env['ir.http']._slug
        url = f"/shop/{slug(self.product.product_tmpl_id)}?extra_param=true"
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200,
                         "Product page should be reachable with extra_param")

    def test_03_combination_info_override(self):
        """Test the _get_combination_info override using a mocked request."""
        # Mocking the request session as the model method depends on it
        mock_request = MagicMock()
        mock_request.session = {'barcode': self.product.barcode}
        
        with patch('odoo.http.request', mock_request):
            # Call the method with is_barcode=True
            res = self.product.product_tmpl_id._get_combination_info(
                is_barcode=True
            )
            # The override updates 'combination' based on the product found by barcode
            self.assertIn('combination', res,
                          "Result should contain 'combination' key when is_barcode is True")
            
            # Verify the combination contains values from our product
            expected_values = self.product.product_template_attribute_value_ids
            self.assertEqual(len(res['combination']), len(expected_values),
                             "Combination should match the product's attribute values")
