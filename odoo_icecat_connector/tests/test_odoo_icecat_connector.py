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
from odoo.tests import TransactionCase, tagged
from odoo.addons.odoo_icecat_connector.controllers.odoo_icecat_connector import IcecatConnector


class MockRequest:
    def __init__(self, env):
        self.env = env


@tagged('post_install', '-at_install')
class TestOdooIcecatConnector(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = IcecatConnector()
        cls.mock_request = MockRequest(cls.env)

        cls.env.company.write({'user_id_icecat': 'test_icecat_user'})
        
        cls.product = cls.env['product.product'].create({
            'name': 'Icecat Product',
            'brand': 'Logitech',
            'default_code': '910-001822',
        })

    def test_01_get_icecat_product_details_success(self):
        """Test successful retrieval of Icecat product details with status True."""
        mock_response_json = {
            'data': {
                'GeneralInfo': {'Description': 'Logitech Mouse'},
            }
        }

        with patch('odoo.addons.odoo_icecat_connector.controllers.odoo_icecat_connector.request', self.mock_request), \
             patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response_json

            res = self.controller.get_icecat_product_details(self.product.id)

            mock_get.assert_any_call(
                "https://live.icecat.biz/api?UserName=test_icecat_user&Language=en&Content=&Brand=Logitech&ProductCode=910-001822"
            )
            self.assertEqual(res['brand'], 'Logitech')
            self.assertEqual(res['product_code'], '910-001822')
            self.assertEqual(res['username'], 'test_icecat_user')
            self.assertTrue(res['status'])

    def test_02_get_icecat_product_details_no_data(self):
        """Test product details retrieval when data key is missing in Icecat API response."""
        mock_response_json = {
            'error': 'Product not found'
        }

        with patch('odoo.addons.odoo_icecat_connector.controllers.odoo_icecat_connector.request', self.mock_request), \
             patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response_json

            res = self.controller.get_icecat_product_details(self.product.id)

            self.assertFalse(res['status'])

    def test_03_get_icecat_product_details_empty_id(self):
        """Test method with empty product_id returns None."""
        res = self.controller.get_icecat_product_details(False)
        self.assertIsNone(res)

    def test_04_fetch_icecat_image(self):
        """Test _fetch_icecat_image fetches and sets image_1920 on product template."""
        mock_api_json = {
            'data': {
                'Image': {
                    'HighPic': 'https://images.icecat.biz/img/norm/high/test.jpg'
                }
            }
        }
        mock_image_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00'
            b'\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        def mock_requests_get(url, **kwargs):
            class MockResponse:
                def __init__(self, status_code, content=None, json_data=None):
                    self.status_code = status_code
                    self.content = content
                    self._json = json_data

                def json(self):
                    return self._json

            if 'live.icecat.biz' in url:
                return MockResponse(200, json_data=mock_api_json)
            elif 'test.jpg' in url:
                return MockResponse(200, content=mock_image_bytes)
            return MockResponse(404)

        with patch('requests.get', side_effect=mock_requests_get):
            product_tmpl = self.env['product.template'].create({
                'name': 'Test Image Product',
                'brand': 'HP',
                'default_code': 'C6050A',
            })
            self.assertTrue(product_tmpl.image_1920)

