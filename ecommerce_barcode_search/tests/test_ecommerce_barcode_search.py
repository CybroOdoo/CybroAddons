# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
import logging
from unittest.mock import MagicMock, patch

from odoo.fields import Command
from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.ecommerce_barcode_search.controllers.web_product_qr_scan import WebsiteProductBarcode

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestEcommerceBarcodeSearch(TransactionCase):
    """Unit and ORM test cases for the ecommerce_barcode_search module.

    Covers:
    - Product template combination info retrieval without barcode.
    - Product template combination info retrieval when barcode is matched from session.
    - Graceful handling of non-existent or empty barcode in session.
    - Controller barcode search logic (session update, redirection URL generation).
    - Controller handling of non-existent barcode.
    - Controller product page route with 'extra_param'.
    - QWeb views registration and content checks.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _logger.info('Setting up TestEcommerceBarcodeSearch class')

        cls.website = cls.env['website'].search([], limit=1)
        if not cls.website:
            cls.website = cls.env['website'].create({
                'name': 'Test Website',
                'company_id': cls.env.company.id,
            })
        cls.pricelist = cls.website.pricelist_id or cls.env['product.pricelist'].search([], limit=1)
        if not cls.website.pricelist_id and cls.pricelist:
            cls.website.pricelist_id = cls.pricelist
        cls.fiscal_position = cls.env['account.fiscal.position'].search([], limit=1) or cls.env['account.fiscal.position']

        # Ensure website context is bound for env.website resolution
        cls.env = cls.env(context=dict(cls.env.context, website_id=cls.website.id))

        # Create standard test product template
        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Simple Product',
            'type': 'consu',
            'list_price': 50.0,
            'barcode': 'TEST_BARCODE_001',
            'website_published': True,
        })
        cls.product = cls.product_template.product_variant_id

        # Create product attribute and values for variant testing
        cls.size_attribute = cls.env['product.attribute'].create({
            'name': 'Size',
            'value_ids': [
                Command.create({'name': 'Small'}),
                Command.create({'name': 'Large'}),
            ],
        })
        cls.template_with_variants = cls.env['product.template'].create({
            'name': 'Test Variant Product',
            'type': 'consu',
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': cls.size_attribute.id,
                    'value_ids': [Command.set(cls.size_attribute.value_ids.ids)],
                }),
            ],
            'website_published': True,
        })
        # Assign distinct barcodes to variants
        cls.variant_small = cls.template_with_variants.product_variant_ids[0]
        cls.variant_small.barcode = 'TEST_BARCODE_SMALL'
        cls.variant_large = cls.template_with_variants.product_variant_ids[1]
        cls.variant_large.barcode = 'TEST_BARCODE_LARGE'

        cls.controller = WebsiteProductBarcode()

    def _mock_request(self, session_data=None):
        """Helper to create a mock request with website_sale required attributes."""
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.website = self.website
        mock_req.pricelist = self.pricelist
        mock_req.fiscal_position = self.fiscal_position
        mock_req.session = session_data if session_data is not None else {}
        return mock_req

    def test_01_get_combination_info_default(self):
        """Standard _get_combination_info call (is_barcode=False) returns valid info."""
        _logger.info('Running test_01_get_combination_info_default')
        mock_req = self._mock_request()
        with patch('odoo.addons.website_sale.models.product_template.request', mock_req), \
             patch('odoo.addons.ecommerce_barcode_search.models.product_template.request', mock_req):
            res = self.product_template._get_combination_info()
            self.assertIn('product_id', res)
            self.assertEqual(res['product_id'], self.product.id)
            self.assertEqual(res['price'], 50.0)

    def test_02_get_combination_info_with_barcode_session(self):
        """_get_combination_info with is_barcode=True retrieves combination from session barcode."""
        _logger.info('Running test_02_get_combination_info_with_barcode_session')
        mock_req = self._mock_request({'barcode': 'TEST_BARCODE_LARGE'})

        with patch('odoo.addons.website_sale.models.product_template.request', mock_req), \
             patch('odoo.addons.ecommerce_barcode_search.models.product_template.request', mock_req):
            res = self.template_with_variants._get_combination_info(is_barcode=True)
            self.assertIn('combination', res)
            expected_ptavs = [each for each in self.variant_large.product_template_attribute_value_ids]
            self.assertEqual(res['combination'], expected_ptavs)

    def test_03_get_combination_info_barcode_not_found(self):
        """_get_combination_info with an unknown barcode should fallback gracefully."""
        _logger.info('Running test_03_get_combination_info_barcode_not_found')
        mock_req = self._mock_request({'barcode': 'NON_EXISTENT_BARCODE'})

        with patch('odoo.addons.website_sale.models.product_template.request', mock_req), \
             patch('odoo.addons.ecommerce_barcode_search.models.product_template.request', mock_req):
            res = self.template_with_variants._get_combination_info(is_barcode=True)
            self.assertIsInstance(res, dict)
            self.assertIn('product_id', res)

    def test_04_get_combination_info_empty_session_barcode(self):
        """_get_combination_info with is_barcode=True and no barcode in session."""
        _logger.info('Running test_04_get_combination_info_empty_session_barcode')
        mock_req = self._mock_request({})

        with patch('odoo.addons.website_sale.models.product_template.request', mock_req), \
             patch('odoo.addons.ecommerce_barcode_search.models.product_template.request', mock_req):
            res = self.product_template._get_combination_info(is_barcode=True)
            self.assertIsInstance(res, dict)
            self.assertEqual(res['product_id'], self.product.id)

    def test_04b_get_combination_info_without_request(self):
        """_get_combination_info with is_barcode=True outside of HTTP request context guards against missing request."""
        _logger.info('Running test_04b_get_combination_info_without_request')
        # Case 1: request is None
        with patch('odoo.addons.ecommerce_barcode_search.models.product_template.request', None):
            res = self.product_template._get_combination_info(
                is_barcode=True,
                pricelist=self.pricelist,
                fiscal_position=self.fiscal_position,
            )
            self.assertIsInstance(res, dict)
            self.assertEqual(res['product_id'], self.product.id)

        # Case 2: request is unbound (accessing session raises RuntimeError)
        unbound_mock = MagicMock()
        type(unbound_mock).session = property(lambda self: (_ for _ in ()).throw(RuntimeError('request not bound')))
        with patch('odoo.addons.ecommerce_barcode_search.models.product_template.request', unbound_mock):
            res = self.product_template._get_combination_info(
                is_barcode=True,
                pricelist=self.pricelist,
                fiscal_position=self.fiscal_position,
            )
            self.assertIsInstance(res, dict)
            self.assertEqual(res['product_id'], self.product.id)

    def test_05_views_templates_presence(self):
        """Verify the template extensions for barcode scanning are present."""
        _logger.info('Running test_05_views_templates_presence')
        view_barcode = self.env.ref('ecommerce_barcode_search.product_barcode')
        self.assertTrue(view_barcode, "Template ecommerce_barcode_search.product_barcode must exist")
        self.assertIn('o_wsale_apply_barcode', view_barcode.arch)
        self.assertIn('barcodeModal', view_barcode.arch)
        self.assertIn('noProductModal', view_barcode.arch)
        self.assertIn('Scan Barcode', view_barcode.arch)

        view_inherit = self.env.ref('ecommerce_barcode_search.website_sale_products_barcode_scan')
        self.assertTrue(view_inherit, "Template website_sale_products_barcode_scan must exist")
        self.assertEqual(view_inherit.name, 'Product Barcode Scan')
        self.assertIn('ecommerce_barcode_search.product_barcode', view_inherit.arch)

    def test_06_controller_product_barcode_found(self):
        """Controller product_barcode should set session data and return action URL."""
        _logger.info('Running test_06_controller_product_barcode_found')
        mock_req = self._mock_request()

        with patch('odoo.addons.ecommerce_barcode_search.controllers.web_product_qr_scan.request', mock_req):
            result = self.controller.product_barcode(last_code='TEST_BARCODE_001')
            self.assertTrue(result)
            self.assertEqual(result.get('type'), 'ir.actions.act_url')
            self.assertIn('extra_param=true', result.get('url', ''))
            self.assertEqual(mock_req.session.get('barcode'), 'TEST_BARCODE_001')
            self.assertEqual(mock_req.session.get('barcode_product'), self.product.id)

    def test_06b_controller_product_barcode_variant_redirect(self):
        """Controller product_barcode for a variant returns URL selecting that variant."""
        _logger.info('Running test_06b_controller_product_barcode_variant_redirect')
        mock_req = self._mock_request()

        with patch('odoo.addons.ecommerce_barcode_search.controllers.web_product_qr_scan.request', mock_req):
            result = self.controller.product_barcode(last_code='TEST_BARCODE_LARGE')
            self.assertTrue(result)
            self.assertEqual(result.get('type'), 'ir.actions.act_url')
            redirect_url = result.get('url', '')
            self.assertIn('extra_param=true', redirect_url)
            slug = self.env['ir.http']._slug
            self.assertIn(slug(self.size_attribute), redirect_url)
            self.assertEqual(mock_req.session.get('barcode_product'), self.variant_large.id)

    def test_07_controller_product_barcode_not_found(self):
        """Controller product_barcode returns False when barcode does not exist."""
        _logger.info('Running test_07_controller_product_barcode_not_found')
        mock_req = self._mock_request()

        with patch('odoo.addons.ecommerce_barcode_search.controllers.web_product_qr_scan.request', mock_req):
            result = self.controller.product_barcode(last_code='UNKNOWN_BARCODE')
            self.assertFalse(result)
            self.assertEqual(mock_req.session.get('barcode'), 'UNKNOWN_BARCODE')
            self.assertFalse(mock_req.session.get('barcode_product'))

    def test_08_controller_product_wiring_combination_info(self):
        """Controller product method calls _get_combination_info(is_barcode=True) when extra_param is true."""
        _logger.info('Running test_08_controller_product_wiring_combination_info')
        endpoint = getattr(WebsiteProductBarcode.product, 'original_endpoint', WebsiteProductBarcode.product)
        mock_response = MagicMock()
        mock_response.qcontext = {}

        mock_req = self._mock_request({'barcode': 'TEST_BARCODE_LARGE'})

        with patch('odoo.addons.website_sale.controllers.main.WebsiteSale.product', return_value=mock_response), \
             patch('odoo.addons.ecommerce_barcode_search.controllers.web_product_qr_scan.request', mock_req), \
             patch('odoo.addons.website_sale.models.product_template.request', mock_req), \
             patch('odoo.addons.ecommerce_barcode_search.models.product_template.request', mock_req):
            # When extra_param is 'true', _get_combination_info(is_barcode=True) is called
            res = endpoint(self.controller, self.template_with_variants, extra_param='true')
            self.assertIn('combination_info', res.qcontext)
            self.assertEqual(res.qcontext['combination_info']['product_id'], self.variant_large.id)
            self.assertEqual(res.qcontext['product_variant'].id, self.variant_large.id)
            # Unused is_barcode_scanned is no longer in qcontext
            self.assertNotIn('is_barcode_scanned', res.qcontext)

            # When extra_param is 'false', combination_info is not updated with is_barcode=True
            mock_response.qcontext = {'combination_info': {'product_id': self.variant_small.id}}
            res = endpoint(self.controller, self.template_with_variants, extra_param='false')
            self.assertEqual(res.qcontext['combination_info']['product_id'], self.variant_small.id)


@tagged('post_install', '-at_install')
class TestEcommerceBarcodeSearchHttp(HttpCase):
    """HTTP integration tests for barcode scanning routes.

    Covers:
    - Public shopper JSON-RPC /shop/barcode/product endpoint (auth="public").
    - Authenticated user JSON-RPC /shop/barcode/product endpoint.
    - Product redirection flow with extra_param query parameter.
    - Shop page rendering with barcode button elements for public and logged-in users.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _logger.info('Setting up TestEcommerceBarcodeSearchHttp class')

        cls.test_user = cls.env['res.users'].create({
            'name': 'Barcode Test User',
            'login': 'barcode_http_user',
            'password': 'barcode_password_123',
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })

        cls.product_template = cls.env['product.template'].create({
            'name': 'HTTP Barcode Product',
            'type': 'consu',
            'list_price': 75.0,
            'barcode': 'HTTP_TEST_BARCODE_777',
            'website_published': True,
        })
        cls.product = cls.product_template.product_variant_id

    def test_09_http_barcode_rpc_found_public_user(self):
        """Public (unauthenticated) shopper can scan and search products via JSON-RPC."""
        _logger.info('Running test_09_http_barcode_rpc_found_public_user')
        # Public session without authentication
        res = self.make_jsonrpc_request(
            '/shop/barcode/product',
            {'last_code': 'HTTP_TEST_BARCODE_777'},
        )
        self.assertTrue(res)
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertIn('extra_param=true', res.get('url', ''))

        # Verify the returned URL is reachable by public shopper
        product_page_res = self.url_open(res['url'])
        self.assertEqual(product_page_res.status_code, 200)

    def test_10_http_barcode_rpc_found_auth_user(self):
        """Authenticated user can perform JSON-RPC barcode search for existing product."""
        _logger.info('Running test_10_http_barcode_rpc_found_auth_user')
        self.authenticate(self.test_user.login, 'barcode_password_123')

        res = self.make_jsonrpc_request(
            '/shop/barcode/product',
            {'last_code': 'HTTP_TEST_BARCODE_777'},
        )
        self.assertTrue(res)
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertIn('extra_param=true', res.get('url', ''))

        # Verify the returned URL is reachable
        product_page_res = self.url_open(res['url'])
        self.assertEqual(product_page_res.status_code, 200)

    def test_11_http_barcode_rpc_not_found_public_user(self):
        """Public shopper JSON-RPC barcode search returns False for missing barcode."""
        _logger.info('Running test_11_http_barcode_rpc_not_found_public_user')
        res = self.make_jsonrpc_request(
            '/shop/barcode/product',
            {'last_code': 'NON_EXISTENT_HTTP_CODE'},
        )
        self.assertFalse(res)

    def test_12_http_shop_page_public_user_has_barcode_elements(self):
        """Public shopper sees barcode scan button and modal on /shop."""
        _logger.info('Running test_12_http_shop_page_public_user_has_barcode_elements')
        response = self.url_open('/shop')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_wsale_apply_barcode', response.text)
        self.assertIn('barcodeModal', response.text)
        self.assertIn('noProductModal', response.text)
