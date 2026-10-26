# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(https://www.cybrosys.com)
#    Author: Cybrosys Techno Solutions(https://www.cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or KIND OF PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging
from odoo.tests import HttpCase, TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestWebsiteProductUomMulti(TransactionCase):
    """Tests for the ``website_product_uom_multi`` addon.
    Covers:
    * Price retrieval with contextual UOM handling.
    * Available UOM calculation.
    * Cart update and UOM‑specific line handling in ``sale.order``.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _logger.info('Setting up TestWebsiteProductUomMulti')
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_pack_6 = cls.env.ref('uom.product_uom_pack_6')

        # Create product template with base UOM = unit and extra UOM = pack of 6
        product_template = cls.env['product.template'].create({
            'name': 'Test Product Multi UOM',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'list_price': 20.0,
            'uom_ids': [(6, 0, [cls.uom_pack_6.id])],
        })
        cls.product = product_template.product_variant_id
        cls.product.write({'uom_ids': [(6, 0, [cls.uom_pack_6.id])]})

        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test Pricelist',
            'currency_id': cls.env.ref('base.USD').id,
        })
        cls.partner.property_product_pricelist = cls.pricelist.id
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
        })

    def test_01_get_contextual_price_with_uom_scaling(self):
        """Verify _get_contextual_price calculates exact price proportionally to UOM ratio."""
        _logger.info('Running test_01_get_contextual_price_with_uom_scaling')
        # Unit price should be 20.0
        unit_price = self.product.with_context(uom=self.uom_unit.id)._get_contextual_price()
        self.assertAlmostEqual(unit_price, 20.0, places=2)

        # Pack of 6 (factor = 6) price should be 120.0 (20 * 6)
        pack_price = self.product.with_context(uom=self.uom_pack_6.id)._get_contextual_price()
        self.assertAlmostEqual(pack_price, 120.0, places=2)

    def test_02_get_available_uoms(self):
        """_get_available_uoms should include both default and configured extra UOMs."""
        _logger.info('Running test_02_get_available_uoms')
        available = self.product._get_available_uoms()
        self.assertIn(self.uom_unit, available)
        self.assertIn(self.uom_pack_6, available)
        self.assertGreaterEqual(len(available), 2)

    def test_03_cart_add_creates_line_with_uom_and_scaled_price(self):
        """Odoo 20 _cart_add creates cart line with selected UOM and computes scaled price unit."""
        _logger.info('Running test_03_cart_add_creates_line_with_uom_and_scaled_price')
        res = self.sale_order._cart_add(
            product_id=self.product.id,
            quantity=1.0,
            uom_id=self.uom_pack_6.id,
        )
        line = self.env['sale.order.line'].browse(res['line_id'])
        self.assertTrue(line.exists())
        self.assertEqual(line.product_uom_id.id, self.uom_pack_6.id)
        self.assertAlmostEqual(line.price_unit, 120.0, places=2)

    def test_04_cart_add_distinct_lines_per_uom(self):
        """Adding same product with different UOMs creates separate cart lines with distinct prices."""
        _logger.info('Running test_04_cart_add_distinct_lines_per_uom')
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
        })
        order._cart_add(product_id=self.product.id, quantity=2.0, uom_id=self.uom_unit.id)
        order._cart_add(product_id=self.product.id, quantity=1.0, uom_id=self.uom_pack_6.id)

        self.assertEqual(len(order.order_line), 2)
        unit_line = order.order_line.filtered(lambda line: line.product_uom_id == self.uom_unit)
        pack_line = order.order_line.filtered(lambda line: line.product_uom_id == self.uom_pack_6)

        self.assertEqual(len(unit_line), 1)
        self.assertEqual(len(pack_line), 1)
        self.assertEqual(unit_line.product_uom_qty, 2.0)
        self.assertAlmostEqual(unit_line.price_unit, 20.0, places=2)
        self.assertEqual(pack_line.product_uom_qty, 1.0)
        self.assertAlmostEqual(pack_line.price_unit, 120.0, places=2)
        # Total: 2 * 20.0 + 1 * 120.0 = 160.0
        self.assertAlmostEqual(order.amount_untaxed, 160.0, places=2)

    def test_05_cart_add_quantity_aggregation_same_uom(self):
        """Adding more quantity of the same UOM aggregates onto existing line without affecting other UOMs."""
        _logger.info('Running test_05_cart_add_quantity_aggregation_same_uom')
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
        })
        order._cart_add(product_id=self.product.id, quantity=1.0, uom_id=self.uom_unit.id)
        order._cart_add(product_id=self.product.id, quantity=1.0, uom_id=self.uom_pack_6.id)
        # Add 2 more packs of 6
        order._cart_add(product_id=self.product.id, quantity=2.0, uom_id=self.uom_pack_6.id)

        self.assertEqual(len(order.order_line), 2)
        unit_line = order.order_line.filtered(lambda line: line.product_uom_id == self.uom_unit)
        pack_line = order.order_line.filtered(lambda line: line.product_uom_id == self.uom_pack_6)

        self.assertEqual(unit_line.product_uom_qty, 1.0)
        self.assertEqual(pack_line.product_uom_qty, 3.0)  # 1 + 2
        # Total: 1 * 20.0 + 3 * 120.0 = 380.0
        self.assertAlmostEqual(order.amount_untaxed, 380.0, places=2)

    def test_06_independent_products_do_not_share_uom(self):
        """Verify UOM selected on one product does not bleed into other products."""
        _logger.info('Running test_06_independent_products_do_not_share_uom')
        other_template = self.env['product.template'].create({
            'name': 'Other Product Default Unit',
            'type': 'consu',
            'uom_id': self.uom_unit.id,
            'list_price': 50.0,
        })
        other_product = other_template.product_variant_id

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
        })
        # Add first product with Pack of 6
        order._cart_add(product_id=self.product.id, quantity=1.0, uom_id=self.uom_pack_6.id)
        # Add second product without specifying UOM - should use its own base UOM (Unit)
        order._cart_add(product_id=other_product.id, quantity=1.0)

        self.assertEqual(len(order.order_line), 2)
        pack_line = order.order_line.filtered(lambda line: line.product_id == self.product)
        other_line = order.order_line.filtered(lambda line: line.product_id == other_product)

        self.assertEqual(pack_line.product_uom_id, self.uom_pack_6)
        self.assertEqual(other_line.product_uom_id, self.uom_unit)
        self.assertAlmostEqual(other_line.price_unit, 50.0, places=2)


@tagged('post_install', '-at_install')
class TestWebsiteProductUomMultiHttp(HttpCase):
    """HTTP and JSON-RPC flow tests for website_product_uom_multi.
    Covers:
    * /website_sale/get_combination_info with UOM selection.
    * /shop/cart/add with UOM propagation.
    * Product isolation (no session leakage to other products).
    * Cart rendering showing the UOM label.
    """

    def setUp(self):
        super().setUp()
        self.uom_unit = self.env.ref('uom.product_uom_unit')
        self.uom_pack_6 = self.env.ref('uom.product_uom_pack_6')

        self.product_template = self.env['product.template'].create({
            'name': 'HTTP Test Product Multi UOM',
            'type': 'consu',
            'uom_id': self.uom_unit.id,
            'list_price': 30.0,
            'uom_ids': [(6, 0, [self.uom_pack_6.id])],
            'website_published': True,
        })
        self.product = self.product_template.product_variant_id
        self.product.write({'uom_ids': [(6, 0, [self.uom_pack_6.id])]})

        self.other_template = self.env['product.template'].create({
            'name': 'HTTP Other Product Base Unit',
            'type': 'consu',
            'uom_id': self.uom_unit.id,
            'list_price': 45.0,
            'website_published': True,
        })
        self.other_product = self.other_template.product_variant_id

    def test_07_http_dropdown_combination_info_to_add_to_cart_flow(self):
        """Test complete RPC flow from combination_info to add-to-cart with UOM scaling and isolation."""
        # Step 1: Simulate dropdown change fetching combination_info for pack of 6
        combination_info = self.make_jsonrpc_request(
            '/website_sale/get_combination_info',
            {
                'product_template_id': self.product_template.id,
                'product_id': self.product.id,
                'combination': [],
                'add_qty': 1.0,
                'uom_id': self.uom_pack_6.id,
            },
        )
        self.assertEqual(combination_info['product_id'], self.product.id)
        # 30.0 * 6 = 180.0
        self.assertAlmostEqual(combination_info['price'], 180.0, places=2)

        # Step 2: Simulate adding to cart with selected UOM (pack of 6)
        add_result = self.make_jsonrpc_request(
            '/shop/cart/add',
            {
                'product_template_id': self.product_template.id,
                'product_id': self.product.id,
                'quantity': 1,
                'uom_id': self.uom_pack_6.id,
            },
        )
        self.assertTrue(add_result.get('cart_quantity') >= 1)

        # Retrieve created cart line and verify it has the requested UOM and scaled price
        cart_line = self.env['sale.order.line'].search([('product_id', '=', self.product.id)], order='id desc', limit=1)
        self.assertTrue(cart_line.exists())
        self.assertEqual(cart_line.product_uom_id, self.uom_pack_6)
        self.assertAlmostEqual(cart_line.price_unit, 180.0, places=2)

        # Step 3: Add second product without UOM; verify no session pollution
        self.make_jsonrpc_request(
            '/shop/cart/add',
            {
                'product_template_id': self.other_template.id,
                'product_id': self.other_product.id,
                'quantity': 1,
            },
        )
        other_cart_line = self.env['sale.order.line'].search([('product_id', '=', self.other_product.id)], order='id desc', limit=1)
        self.assertTrue(other_cart_line.exists())
        self.assertEqual(other_cart_line.product_uom_id, self.uom_unit)
        self.assertAlmostEqual(other_cart_line.price_unit, 45.0, places=2)

        # Step 4: Render cart page to verify UOM label appears
        cart_response = self.url_open('/shop/cart')
        self.assertEqual(cart_response.status_code, 200)
        self.assertIn('o_wsale_uom_label', cart_response.text)
        self.assertIn(self.uom_pack_6.name, cart_response.text)

    def test_08_http_product_page_renders_with_uom_dropdown(self):
        """Test that the eCommerce product detail page renders successfully (HTTP 200)
        and includes the UOM selection dropdown and options without crashing."""
        url = f"/shop/{self.product_template.id}"
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_uom_dropdown', response.text)
        self.assertIn(self.uom_pack_6.name, response.text)

