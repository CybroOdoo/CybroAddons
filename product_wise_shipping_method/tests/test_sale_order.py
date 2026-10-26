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

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import ProductWiseShippingCommon


@tagged('post_install', '-at_install')
class TestSaleOrder(ProductWiseShippingCommon):

    # ------------------------------------------------------------------
    # action_confirm
    # ------------------------------------------------------------------
    def test_confirm_without_shipping_method_adds_no_line(self):
        order = self._create_order(self.product_plain)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertEqual(len(order.order_line), 1)

    def test_confirm_adds_delivery_line(self):
        order = self._create_order(self.product_a1)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertEqual(len(order.order_line), 2)
        delivery = self._lines_for(order, self.ship_product_a)
        self.assertEqual(len(delivery), 1)
        self.assertEqual(delivery.product_uom_qty, 1.0)
        self.assertEqual(delivery.price_unit, self.ship_product_a.list_price)
        self.assertEqual(delivery.product_uom_id, self.ship_product_a.uom_id)
        self.assertIn(self.carrier_a.name, delivery.name)

    def test_delivery_line_is_per_line_not_per_quantity(self):
        order = self._create_order(self.product_a1, qty=5.0)
        order.action_confirm()
        delivery = self._lines_for(order, self.ship_product_a)
        self.assertEqual(len(delivery), 1)
        self.assertEqual(delivery.product_uom_qty, 1.0)

    def test_same_carrier_lines_are_merged(self):
        order = self._create_order(self.product_a1 | self.product_a2)
        self.assertEqual(len(order.order_line), 2)
        order.action_confirm()
        delivery = self._lines_for(order, self.ship_product_a)
        self.assertEqual(len(delivery), 1)
        self.assertEqual(delivery.product_uom_qty, 2.0)
        self.assertEqual(len(order.order_line), 3)

    def test_different_carriers_give_separate_lines(self):
        order = self._create_order(self.product_a1 | self.product_b1)
        order.action_confirm()
        delivery_a = self._lines_for(order, self.ship_product_a)
        delivery_b = self._lines_for(order, self.ship_product_b)
        self.assertEqual(len(delivery_a), 1)
        self.assertEqual(len(delivery_b), 1)
        self.assertEqual(delivery_a.product_uom_qty, 1.0)
        self.assertEqual(delivery_b.product_uom_qty, 1.0)
        self.assertEqual(delivery_b.price_unit, self.ship_product_b.list_price)
        self.assertEqual(len(order.order_line), 4)

    def test_mixed_products(self):
        order = self._create_order(
            self.product_a1 | self.product_plain | self.product_b1)
        order.action_confirm()
        self.assertEqual(len(order.order_line), 5)
        self.assertEqual(len(self._lines_for(order, self.ship_product_a)), 1)
        self.assertEqual(len(self._lines_for(order, self.ship_product_b)), 1)

    def test_duplicated_lines_get_no_delivery_line(self):
        order = self._create_order(self.product_a1)
        order.order_line.is_duplicated = True
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertFalse(self._lines_for(order, self.ship_product_a))
        self.assertEqual(len(order.order_line), 1)

    def test_website_order_skips_shipping_logic(self):
        website = self.env['website'].search([], limit=1)
        if not website:
            website = self.env['website'].create({'name': 'PWSM Website'})
        order = self._create_order(self.product_a1, website_id=website.id)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertFalse(self._lines_for(order, self.ship_product_a))
        self.assertEqual(len(order.order_line), 1)

    # ------------------------------------------------------------------
    # merge_similar_products / create / write
    # ------------------------------------------------------------------
    def test_create_merges_same_product_lines(self):
        variant = self.product_plain.product_variant_id
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create(
                    {'product_id': variant.id, 'product_uom_qty': 1}),
                Command.create(
                    {'product_id': variant.id, 'product_uom_qty': 2}),
            ],
        })
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line.product_uom_qty, 3.0)

    def test_create_keeps_different_products_separate(self):
        order = self._create_order(self.product_plain | self.product_a1)
        self.assertEqual(len(order.order_line), 2)

    def test_write_merges_new_line_into_existing(self):
        order = self._create_order(self.product_plain)
        order.write({'order_line': [Command.create({
            'product_id': self.product_plain.product_variant_id.id,
            'product_uom_qty': 2,
        })]})
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line.product_uom_qty, 3.0)

    def test_write_keeps_different_product_separate(self):
        order = self._create_order(self.product_plain)
        order.write({'order_line': [Command.create({
            'product_id': self.product_a1.product_variant_id.id,
            'product_uom_qty': 1,
        })]})
        self.assertEqual(len(order.order_line), 2)

    def test_merge_similar_products_direct_call(self):
        order = self._create_order(self.product_plain | self.product_b1)
        order.merge_similar_products()
        self.assertEqual(len(order.order_line), 2)

    def test_section_and_note_lines_are_not_merged(self):
        order = self._create_order(self.product_plain)
        order.write({'order_line': [
            Command.create({'display_type': 'line_section', 'name': 'One'}),
            Command.create({'display_type': 'line_section', 'name': 'Two'}),
            Command.create({'display_type': 'line_note', 'name': 'Note'}),
        ]})
        self.assertEqual(len(order.order_line), 4)

    def test_different_discount_lines_are_not_merged(self):
        order = self._create_order(self.product_plain)
        order.write({'order_line': [Command.create({
            'product_id': self.product_plain.product_variant_id.id,
            'product_uom_qty': 1,
            'discount': 10.0,
        })]})
        self.assertEqual(len(order.order_line), 2)

    def test_different_description_lines_are_not_merged(self):
        order = self._create_order(self.product_plain)
        order.write({'order_line': [Command.create({
            'product_id': self.product_plain.product_variant_id.id,
            'product_uom_qty': 1,
            'name': 'Custom description',
        })]})
        self.assertEqual(len(order.order_line), 2)

    def test_confirmed_order_lines_are_not_merged_or_unlinked(self):
        order = self._create_order(self.product_plain)
        order.action_confirm()
        order.write({'order_line': [Command.create({
            'product_id': self.product_plain.product_variant_id.id,
            'product_uom_qty': 1,
        })]})
        self.assertEqual(len(order.order_line), 2)
        order.merge_similar_products()
        self.assertEqual(len(order.order_line), 2)

    def test_merge_does_not_mix_lines_of_different_orders(self):
        order_1 = self._create_order(self.product_plain)
        order_2 = self._create_order(self.product_plain)
        (order_1 | order_2).merge_similar_products()
        self.assertEqual(len(order_1.order_line), 1)
        self.assertEqual(len(order_2.order_line), 1)

    def test_confirm_multiple_orders(self):
        order_1 = self._create_order(self.product_a1)
        order_2 = self._create_order(self.product_b1)
        orders = order_1 | order_2
        orders.action_confirm()
        self.assertEqual(set(orders.mapped('state')), {'sale'})
        self.assertEqual(len(self._lines_for(order_1, self.ship_product_a)), 1)
        self.assertFalse(self._lines_for(order_1, self.ship_product_b))
        self.assertEqual(len(self._lines_for(order_2, self.ship_product_b)), 1)
        self.assertFalse(self._lines_for(order_2, self.ship_product_a))

    # ------------------------------------------------------------------
    # copy
    # ------------------------------------------------------------------
    def test_original_lines_are_not_flagged_duplicated(self):
        order = self._create_order(self.product_a1)
        self.assertFalse(any(order.order_line.mapped('is_duplicated')))

    def test_copy_flags_lines_as_duplicated(self):
        order = self._create_order(self.product_a1 | self.product_plain)
        new_order = order.copy()
        self.assertNotEqual(new_order, order)
        self.assertTrue(new_order.order_line)
        self.assertTrue(all(new_order.order_line.mapped('is_duplicated')))
        self.assertFalse(any(order.order_line.mapped('is_duplicated')))

    def test_confirm_copied_order_adds_no_new_delivery_line(self):
        order = self._create_order(self.product_a1)
        order.action_confirm()
        new_order = order.copy()
        self.assertEqual(new_order.state, 'draft')
        self.assertTrue(all(new_order.order_line.mapped('is_duplicated')))
        before = sum(self._lines_for(
            new_order, self.ship_product_a).mapped('product_uom_qty'))
        new_order.action_confirm()
        self.assertEqual(new_order.state, 'sale')
        after = sum(self._lines_for(
            new_order, self.ship_product_a).mapped('product_uom_qty'))
        self.assertEqual(before, after)

    # ------------------------------------------------------------------
    # action_open_delivery_wizard
    # ------------------------------------------------------------------
    def test_delivery_wizard_blocked_when_product_has_shipping_method(self):
        order = self._create_order(self.product_a1)
        with self.assertRaisesRegex(UserError, 'already applied'):
            order.action_open_delivery_wizard()

    def test_delivery_wizard_blocked_if_any_line_has_shipping_method(self):
        order = self._create_order(self.product_plain | self.product_b1)
        with self.assertRaises(UserError):
            order.action_open_delivery_wizard()

    def test_delivery_wizard_opens_without_shipping_products(self):
        order = self._create_order(self.product_plain)
        action = order.action_open_delivery_wizard()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'choose.delivery.carrier')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['default_order_id'], order.id)
        # Expected carrier follows the module logic: the shipping partner's
        # property, else its commercial partner's (may be pre-set by the DB).
        partner = order.partner_shipping_id
        commercial = partner.commercial_partner_id
        expected = (partner.property_delivery_carrier_id
                    or commercial.property_delivery_carrier_id)
        self.assertEqual(
            action['context']['default_carrier_id'], expected.id)

    def test_delivery_wizard_uses_partner_default_carrier(self):
        self.partner.property_delivery_carrier_id = self.carrier_b
        order = self._create_order(self.product_plain)
        action = order.action_open_delivery_wizard()
        self.assertEqual(
            action['context']['default_carrier_id'], self.carrier_b.id)
