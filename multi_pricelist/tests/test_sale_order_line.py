# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: K Sai Saran Varma (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSaleOrderLine(TransactionCase):
    """Test cases for sale.order.line multi_pricelist extension"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        # Reuse an existing product to avoid the NOT NULL constraint on
        # publish_date that a website-related module adds to product_template.
        cls.product = cls.env['product.product'].search(
            [('sale_ok', '=', True)], limit=1
        )
        if not cls.product:
            cls.product = cls.env['product.product'].search([], limit=1)

        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test Pricelist',
        })

        cls.pricelist_item = cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.pricelist.id,
            'applied_on': '0_product_variant',
            'product_id': cls.product.id,
            'compute_price': 'fixed',
            'fixed_price': 80,
            'min_quantity': 1,
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
        })

        cls.order_line = cls.env['sale.order.line'].create({
            'order_id': cls.sale_order.id,
            'product_id': cls.product.id,
            'product_uom_qty': 1,
            'price_unit': 100,
            'name': cls.product.name,
        })

    # ------------------------------------------------------------------
    # _compute_pricelist_visibility
    # ------------------------------------------------------------------

    def test_pricelist_visibility_enabled(self):
        """Visibility is True when config param is set and order is draft"""

        self.env['ir.config_parameter'].sudo().set_param(
            'multi_pricelist.multi_pricelist', 'True'
        )

        self.order_line._compute_pricelist_visibility()

        self.assertTrue(
            self.order_line.pricelist_visibility,
            "pricelist_visibility should be True when param is set and order is draft",
        )

    def test_pricelist_visibility_hidden_on_confirmed_order(self):
        """Visibility is False once the order is confirmed (state='sale')"""

        self.env['ir.config_parameter'].sudo().set_param(
            'multi_pricelist.multi_pricelist', 'True'
        )

        # Force state without going through the full confirmation workflow
        self.sale_order.write({'state': 'sale'})

        self.order_line._compute_pricelist_visibility()

        self.assertFalse(
            self.order_line.pricelist_visibility,
            "pricelist_visibility should be False when order state is 'sale'",
        )

        # Reset state for subsequent tests
        self.sale_order.write({'state': 'draft'})

    def test_pricelist_visibility_hidden_on_cancelled_order(self):
        """Visibility is False when order state is 'cancel'"""

        self.sale_order.write({'state': 'cancel'})

        self.order_line._compute_pricelist_visibility()

        self.assertFalse(
            self.order_line.pricelist_visibility,
            "pricelist_visibility should be False when order state is 'cancel'",
        )

        self.sale_order.write({'state': 'draft'})

    # ------------------------------------------------------------------
    # _get_pricelist_price
    # ------------------------------------------------------------------

    def test_get_pricelist_price_with_applied_pricelist(self):
        """_get_pricelist_price returns a numeric value when a pricelist is set"""

        self.order_line.write({'applied_pricelist_id': self.pricelist.id})

        price = self.order_line._get_pricelist_price()

        self.assertIsInstance(price, (int, float))
        self.assertGreaterEqual(price, 0)

    def test_get_pricelist_price_without_applied_pricelist(self):
        """_get_pricelist_price falls back gracefully when no custom pricelist set"""
        self.order_line.write({'applied_pricelist_id': False})

        # Should not raise; result depends on default pricelist item
        price = self.order_line._get_pricelist_price()

        self.assertIsInstance(price, (int, float))

    # ------------------------------------------------------------------
    # apply_pricelist (wizard action)
    # ------------------------------------------------------------------

    def test_apply_pricelist_returns_action(self):
        """apply_pricelist returns an act_window action for pricelist.product"""
        action = self.order_line.apply_pricelist()

        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'pricelist.product')
        self.assertEqual(action.get('target'), 'new')

    def test_apply_pricelist_no_matching_item_raises(self):
        """apply_pricelist raises UserError when no pricelist item covers product"""

        # Find a second product that has NO pricelist items configured
        other_product = self.env['product.product'].search(
            [('id', '!=', self.product.id), ('sale_ok', '=', True)],
            limit=1
        )

        if not other_product:
            self.skipTest(
                "No second saleable product available for this test"
            )

        # Remove any existing pricelist items for this product
        self.env['product.pricelist.item'].search([
            ('product_id', '=', other_product.id)
        ]).unlink()

        self.env['product.pricelist.item'].search([
            ('product_tmpl_id', '=', other_product.product_tmpl_id.id)
        ]).unlink()

        line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': other_product.id,
            'product_uom_qty': 1,
            'price_unit': 200,
            'name': other_product.name,
        })

        with self.assertRaises(UserError):
            line.apply_pricelist()

    # ------------------------------------------------------------------
    # unit_price helper
    # ------------------------------------------------------------------

    def test_unit_price_fixed(self):
        """unit_price returns fixed_price for 'fixed' compute_price items"""

        price = self.order_line.unit_price(self.pricelist_item)

        self.assertAlmostEqual(price, 80.0)

    def test_unit_price_percentage(self):
        """unit_price applies percent discount correctly"""

        item = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '0_product_variant',
            'product_id': self.product.id,
            'compute_price': 'percentage',
            'percent_price': 10,
            'min_quantity': 1,
        })

        expected = self.product.list_price * (1 - 10 / 100)

        price = self.order_line.unit_price(item)

        self.assertAlmostEqual(price, expected)

    def test_unit_price_formula_list_price(self):
        """unit_price handles formula based on list_price"""

        item = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '0_product_variant',
            'product_id': self.product.id,
            'compute_price': 'formula',
            'base': 'list_price',
            'price_discount': 10,
            'price_surcharge': 5,
            'min_quantity': 1,
        })

        expected = (
                self.product.list_price * (1 - 10 / 100) + 5
        )

        price = self.order_line.unit_price(item)

        self.assertAlmostEqual(price, expected)

    def test_unit_price_formula_standard_price(self):
        """unit_price handles formula based on standard_price (cost)"""

        item = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '0_product_variant',
            'product_id': self.product.id,
            'compute_price': 'formula',
            'base': 'standard_price',
            'price_discount': 0,
            'price_surcharge': 0,
            'min_quantity': 1,
        })

        expected = self.product.standard_price

        price = self.order_line.unit_price(item)

        self.assertAlmostEqual(price, expected)

    def test_unit_price_fallback(self):
        """unit_price returns list_price when no specific rule matches"""

        # Create a percentage item with 0 percent (falls to else branch)
        item = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '0_product_variant',
            'product_id': self.product.id,
            'compute_price': 'percentage',
            'percent_price': 0,
            'min_quantity': 1,
        })

        price = self.order_line.unit_price(item)

        self.assertAlmostEqual(price, self.product.list_price)
