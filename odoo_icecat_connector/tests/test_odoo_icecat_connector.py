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

from unittest.mock import patch
import requests
from odoo.tests import TransactionCase, tagged
from odoo.addons.odoo_icecat_connector.controllers.odoo_icecat_connector import IcecatConnector

VALID_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0'
    b'\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82'
)


class MockRequest:
    """Mock request wrapper providing access to an Odoo environment and optional website."""

    def __init__(self, env, website=None):
        """Initialize mock request with an environment and optional website."""
        self.env = env
        self.website = website


class MockResponse:
    """Simulated HTTP response object for requests mocking."""

    def __init__(self, status_code, content=None, json_data=None):
        """Initialize simulated response status code, raw content, and json."""
        self.status_code = status_code
        self.content = content
        self._json = json_data

    def json(self):
        """Return the parsed JSON dictionary payload."""
        return self._json


@tagged('post_install', '-at_install')
class TestOdooIcecatConnector(TransactionCase):
    """Test suite for Odoo Icecat Connector controller and model operations."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment, controller, and sample product."""
        super().setUpClass()
        cls.controller = IcecatConnector()
        cls.mock_request = MockRequest(cls.env)

        cls.env.company.write({'user_id_icecat': 'test_icecat_user'})

        cls.product = cls.env['product.product'].create({
            'name': 'Icecat Product',
            'brand': 'Logitech',
            'default_code': '910-001822',
            'website_published': True,
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
                "https://live.icecat.biz/api",
                params={
                    'UserName': 'test_icecat_user',
                    'Language': 'en',
                    'Content': '',
                    'Brand': 'Logitech',
                    'ProductCode': '910-001822',
                },
                timeout=10,
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

    def test_04_get_icecat_product_details_nonexistent_product(self):
        """Test method with nonexistent product_id returns status False."""
        with patch('odoo.addons.odoo_icecat_connector.controllers.odoo_icecat_connector.request', self.mock_request):
            res = self.controller.get_icecat_product_details(999999999)
            self.assertEqual(res, {'status': False})

    def test_05_get_icecat_product_details_network_error(self):
        """Test method when requests.get raises an exception."""
        with patch('odoo.addons.odoo_icecat_connector.controllers.odoo_icecat_connector.request', self.mock_request), \
             patch('requests.get', side_effect=requests.exceptions.ConnectionError("Network down")):
            res = self.controller.get_icecat_product_details(self.product.id)
            self.assertEqual(res, {'status': False})

    def test_06_fetch_icecat_image(self):
        """Test _fetch_icecat_image fetches and sets image_1920 on product template."""
        mock_api_json = {
            'data': {
                'Image': {
                    'HighPic': 'https://images.icecat.biz/img/norm/high/test.jpg'
                }
            }
        }

        def mock_requests_get(url, **kwargs):
            """Mock requests.get call returning simulated Icecat image API response."""
            if 'live.icecat.biz' in url:
                return MockResponse(200, json_data=mock_api_json)
            elif 'test.jpg' in url:
                return MockResponse(200, content=VALID_PNG)
            return MockResponse(404)

        with patch('requests.get', side_effect=mock_requests_get):
            product_tmpl = self.env['product.template'].create({
                'name': 'Test Image Product',
                'brand': 'HP',
                'default_code': 'C6050A',
            })
            product_tmpl._fetch_icecat_image()
            self.assertTrue(product_tmpl.image_1920)

    def test_07_action_fetch_icecat_image(self):
        """Test action_fetch_icecat_image manually triggers image fetch."""
        product_tmpl = self.env['product.template'].create({
            'name': 'Manual Fetch Product',
        })
        self.assertFalse(product_tmpl.image_1920)

        mock_api_json = {
            'data': {
                'Image': {
                    'HighPic': 'https://images.icecat.biz/img/norm/high/manual.jpg'
                }
            }
        }

        def mock_requests_get(url, **kwargs):
            """Mock requests.get call returning simulated manual fetch API response."""
            if 'live.icecat.biz' in url:
                return MockResponse(200, json_data=mock_api_json)
            elif 'manual.jpg' in url:
                return MockResponse(200, content=VALID_PNG)
            return MockResponse(404)

        with patch('requests.get', side_effect=mock_requests_get):
            product_tmpl.write({
                'brand': 'Canon',
                'default_code': 'CAN-001',
            })
            product_tmpl.image_1920 = False
            product_tmpl.action_fetch_icecat_image()
            self.assertTrue(product_tmpl.image_1920)

    def test_08_res_config_settings_user_id(self):
        """Test setting and retrieving Icecat user id via res.config.settings."""
        settings = self.env['res.config.settings'].create({
            'user_id_icecat': 'new_user_123',
        })
        settings.execute()
        self.assertEqual(self.env.company.user_id_icecat, 'new_user_123')

    def test_09_get_icecat_product_details_unpublished(self):
        """Test unpublished product returns status False without making an API call."""
        unpublished_product = self.env['product.product'].create({
            'name': 'Unpublished Product',
            'brand': 'Logitech',
            'default_code': 'UNPUB-001',
            'website_published': False,
        })
        with patch('odoo.addons.odoo_icecat_connector.controllers.odoo_icecat_connector.request', self.mock_request), \
             patch('requests.get') as mock_get:
            res = self.controller.get_icecat_product_details(unpublished_product.id)
            mock_get.assert_not_called()
            self.assertEqual(res, {'status': False})

    def test_10_get_icecat_product_details_website_company(self):
        """Test that company is resolved from request.website.company_id."""
        second_company = self.env['res.company'].create({
            'name': 'Website Company',
            'user_id_icecat': 'website_specific_user',
        })
        website = self.env['website'].create({
            'name': 'Branch Website',
            'company_id': second_company.id,
        })
        request_with_website = MockRequest(self.env, website=website)

        mock_response_json = {
            'data': {
                'GeneralInfo': {'Description': 'Website Company Product'},
            }
        }

        with patch('odoo.addons.odoo_icecat_connector.controllers.odoo_icecat_connector.request', request_with_website), \
             patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response_json

            res = self.controller.get_icecat_product_details(self.product.id)

            mock_get.assert_called_with(
                'https://live.icecat.biz/api',
                params={
                    'UserName': 'website_specific_user',
                    'Language': 'en',
                    'Content': '',
                    'Brand': 'Logitech',
                    'ProductCode': '910-001822',
                },
                timeout=10,
            )
            self.assertEqual(res['username'], 'website_specific_user')
            self.assertTrue(res['status'])

    def test_11_fetch_icecat_image_missing_fields(self):
        """Test _fetch_icecat_image cleanly skips products without brand or code."""
        product_no_brand = self.env['product.template'].create({
            'name': 'No Brand Product',
            'default_code': 'CODE123',
        })
        product_no_code = self.env['product.template'].create({
            'name': 'No Code Product',
            'brand': 'Logitech',
        })
        with patch('requests.get') as mock_get:
            product_no_brand._fetch_icecat_image()
            product_no_code._fetch_icecat_image()
            mock_get.assert_not_called()
        self.assertFalse(product_no_brand.image_1920)
        self.assertFalse(product_no_code.image_1920)

    def test_12_set_image_from_icecat_data_fallback_urls(self):
        """Test fallback image extraction from Pic500Url and GeneralInfo."""
        tmpl = self.env['product.template'].create({'name': 'Fallback Image Product'})
        data_pic500 = {
            'Image': {'Pic500Url': 'https://images.icecat.biz/img/norm/med/pic500.jpg'},
        }
        with patch('requests.get') as mock_get:
            mock_get.return_value = MockResponse(200, content=VALID_PNG)
            tmpl._set_image_from_icecat_data(data_pic500)
            mock_get.assert_called_with('https://images.icecat.biz/img/norm/med/pic500.jpg', timeout=10)
            self.assertTrue(tmpl.image_1920)

    def test_13_get_icecat_product_details_product_company(self):
        """Test that company falls back to product.company_id when website is None."""
        third_company = self.env['res.company'].create({
            'name': 'Product Specific Company',
            'user_id_icecat': 'product_company_user',
        })
        company_product = self.env['product.product'].create({
            'name': 'Company Specific Product',
            'brand': 'Dell',
            'default_code': 'DELL-999',
            'company_id': third_company.id,
            'website_published': True,
        })
        request_no_website = MockRequest(self.env, website=None)
        mock_response_json = {
            'data': {'GeneralInfo': {'Description': 'Dell Server'}},
        }
        with patch('odoo.addons.odoo_icecat_connector.controllers.odoo_icecat_connector.request', request_no_website), \
             patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response_json

            res = self.controller.get_icecat_product_details(company_product.id)
            mock_get.assert_called_with(
                'https://live.icecat.biz/api',
                params={
                    'UserName': 'product_company_user',
                    'Language': 'en',
                    'Content': '',
                    'Brand': 'Dell',
                    'ProductCode': 'DELL-999',
                },
                timeout=10,
            )
            self.assertEqual(res['username'], 'product_company_user')
            self.assertTrue(res['status'])
