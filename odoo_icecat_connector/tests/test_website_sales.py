# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch
import requests
from odoo.tests import TransactionCase, tagged
from odoo.addons.odoo_icecat_connector.controllers.website_sales import Icecat


class MockRequest:
    def __init__(self, env):
        self.env = env


@tagged('post_install', '-at_install')
class TestWebsiteSales(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = Icecat()
        cls.mock_request = MockRequest(cls.env)
        
        cls.product = cls.env['product.template'].create({
            'name': 'Website Icecat Product',
            'brand': 'Logitech',
            'default_code': '910-001822',
        })
        
        cls.category = cls.env['product.public.category'].create({
            'name': 'Test Category',
        })

    def setUp(self):
        super().setUp()
        self.env.company.write({'user_id_icecat': False})

    def test_01_prepare_product_values_no_username(self):
        """Test _prepare_product_values when icecat user ID is not configured."""
        with patch('odoo.addons.odoo_icecat_connector.controllers.website_sales.request', self.mock_request), \
             patch('odoo.addons.website_sale.controllers.main.WebsiteSale._prepare_product_values', return_value={'base_key': 'base_value'}), \
             patch('requests.get') as mock_get:
            
            res = self.controller._prepare_product_values(self.product, self.category)
            
            mock_get.assert_not_called()
            self.assertIn('base_key', res)
            self.assertNotIn('icecat', res)
            self.assertNotIn('icecat_error', res)

    def test_02_prepare_product_values_success(self):
        """Test _prepare_product_values when icecat user ID is configured and API returns valid data."""
        self.env.company.write({'user_id_icecat': 'website_icecat_user'})
        mock_response_json = {
            'data': {
                'Image': 'http://image.url',
            }
        }

        def mock_get(url, timeout=5):
            class MockResponse:
                def __init__(self, status_code, content=None, json_data=None):
                    self.status_code = status_code
                    self.content = content
                    self._json = json_data

                def json(self):
                    return self._json

            if 'live.icecat.biz' in url:
                return MockResponse(200, json_data=mock_response_json)
            elif 'http://image.url' in url:
                return MockResponse(200, content=(
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                    b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00'
                    b'\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
                ))
            return MockResponse(404)

        with patch('odoo.addons.odoo_icecat_connector.controllers.website_sales.request', self.mock_request), \
             patch('odoo.addons.website_sale.controllers.main.WebsiteSale._prepare_product_values', return_value={'base_key': 'base_value'}), \
             patch('requests.get', side_effect=mock_get):
            
            res = self.controller._prepare_product_values(self.product, self.category)

            self.assertEqual(res['base_key'], 'base_value')
            self.assertEqual(res['icecat'], {'Image': 'http://image.url'})
            self.assertNotIn('icecat_error', res)
            self.assertTrue(self.product.image_1920)

    def test_03_prepare_product_values_api_error(self):
        """Test _prepare_product_values when the Icecat API request fails/times out."""
        self.env.company.write({'user_id_icecat': 'website_icecat_user'})

        with patch('odoo.addons.odoo_icecat_connector.controllers.website_sales.request', self.mock_request), \
             patch('odoo.addons.website_sale.controllers.main.WebsiteSale._prepare_product_values', return_value={'base_key': 'base_value'}), \
             patch('requests.get', side_effect=requests.exceptions.Timeout("Connection timed out")):
            
            res = self.controller._prepare_product_values(self.product, self.category)

            self.assertEqual(res['base_key'], 'base_value')
            self.assertNotIn('icecat', res)
            self.assertIn('icecat_error', res)
            self.assertIn("Connection timed out", res['icecat_error'])
