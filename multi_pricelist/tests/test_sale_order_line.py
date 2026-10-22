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

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
            'standard_price': 60.0,
        })

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

        self.env['ir.config_parameter'].sudo().set_str(
            'multi_pricelist.multi_pricelist', 'True'
        )

        self.order_line._compute_pricelist_visibility()

        self.assertTrue(
            self.order_line.pricelist_visibility,
            "pricelist_visibility should be True when param is set and order is draft",
        )

    def test_pricelist_visibility_hidden_on_confirmed_order(self):
        """Visibility is False once the order is confirmed (state='sale')"""

        self.env['ir.config_parameter'].sudo().set_str(
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
        """_get_pricelist_price uses the pricelist applied on the line"""
        cheaper = self.env['product.pricelist'].create({'name': 'Cheaper'})
        cheaper_item = self.env['product.pricelist.item'].create({
            'pricelist_id': cheaper.id,
            'applied_on': '0_product_variant',
            'product_id': self.product.id,
            'compute_price': 'fixed',
            'fixed_price': 50,
            'min_quantity': 1,
        })

        self.order_line.write({'applied_pricelist_id': self.pricelist.id})
        self.assertAlmostEqual(self.order_line._get_pricelist_price(), 80.0)

        self.order_line.write({'applied_pricelist_id': cheaper.id})
        self.assertAlmostEqual(self.order_line._get_pricelist_price(), 50.0)
        self.assertEqual(self.order_line.pricelist_item_id, cheaper_item)

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

    def test_apply_pricelist_wizard_lines(self):
        """The wizard has one line per matching pricelist with its price"""
        action = self.order_line.apply_pricelist()
        wizard = self.env['pricelist.product'].browse(action['res_id'])
        line = wizard.line_ids.filtered(
            lambda wizard_line: wizard_line.pricelist_id == self.pricelist)

        self.assertEqual(len(line), 1)
        self.assertAlmostEqual(line.unit_price, 80.0)
        self.assertAlmostEqual(line.unit_cost, 60.0)
        self.assertEqual(line.uom_id, self.order_line.product_uom_id)

    def test_apply_pricelist_ignores_archived_pricelist(self):
        """Archived pricelists are not offered in the wizard"""
        archived = self.env['product.pricelist'].create({
            'name': 'Archived', 'active': False})
        self.env['product.pricelist.item'].create({
            'pricelist_id': archived.id,
            'applied_on': '0_product_variant',
            'product_id': self.product.id,
            'compute_price': 'fixed',
            'fixed_price': 10,
            'min_quantity': 1,
        })

        action = self.order_line.apply_pricelist()
        wizard = self.env['pricelist.product'].browse(action['res_id'])

        self.assertNotIn(archived, wizard.line_ids.pricelist_id)

    def test_apply_pricelist_ignores_other_company_pricelist(self):
        """Pricelists of another company are not offered in the wizard"""
        other_company = self.env['res.company'].create({'name': 'Other Co'})
        foreign = self.env['product.pricelist'].create({
            'name': 'Foreign', 'company_id': other_company.id})
        self.env['product.pricelist.item'].create({
            'pricelist_id': foreign.id,
            'applied_on': '0_product_variant',
            'product_id': self.product.id,
            'compute_price': 'fixed',
            'fixed_price': 10,
            'min_quantity': 1,
        })

        action = self.order_line.apply_pricelist()
        wizard = self.env['pricelist.product'].browse(action['res_id'])

        self.assertNotIn(foreign, wizard.line_ids.pricelist_id)

    def test_apply_pricelist_requires_single_line(self):
        """apply_pricelist is a per-line action"""
        other_line = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'price_unit': 100,
        })

        with self.assertRaises(ValueError):
            (self.order_line | other_line).apply_pricelist()

    def test_apply_pricelist_without_product_raises(self):
        """Section/note lines have no product, so no pricelist can apply"""
        section = self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'display_type': 'line_section',
            'name': 'Section',
        })

        with self.assertRaises(UserError):
            section.apply_pricelist()

    def test_apply_pricelist_no_matching_item_raises(self):
        """apply_pricelist raises UserError when no pricelist has a rule"""
        self.env['product.pricelist.item'].search([]).unlink()

        with self.assertRaises(UserError):
            self.order_line.apply_pricelist()

    # ------------------------------------------------------------------
    # unit_price helper
    # ------------------------------------------------------------------

    def test_unit_price_fixed(self):
        """unit_price returns fixed_price for 'fixed' compute_price items"""

        price = self.order_line.unit_price(self.pricelist_item)

        self.assertAlmostEqual(price, 80.0)

    # ------------------------------------------------------------------
    # settings toggle -> visibility
    # ------------------------------------------------------------------

    def test_pricelist_visibility_follows_settings_toggle(self):
        """Switching the setting off hides the button again"""
        self.env['res.config.settings'].create(
            {'multi_pricelist': True}).set_values()
        self.order_line.invalidate_recordset(['pricelist_visibility'])
        self.assertTrue(self.order_line.pricelist_visibility)

        self.env['res.config.settings'].create(
            {'multi_pricelist': False}).set_values()
        self.order_line.invalidate_recordset(['pricelist_visibility'])
        self.assertFalse(self.order_line.pricelist_visibility)

    def test_pricelist_visibility_disabled_by_default(self):
        """No config parameter means the feature is off"""
        self.env['ir.config_parameter'].sudo().set_str(
            'multi_pricelist.multi_pricelist', 'False')
        self.order_line.invalidate_recordset(['pricelist_visibility'])

        self.assertFalse(self.order_line.pricelist_visibility)
