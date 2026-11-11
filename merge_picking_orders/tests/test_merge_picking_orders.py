# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestMergePickingOrders(TransactionCase):
    """Test suite for merging pickings,

    covering the list view action, the wizard, merging into a new picking or
    an existing one, the stock moves after the merge and the validation
    rules on partners, types and states.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.supplier_location = cls.env.ref('stock.stock_location_suppliers')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Merge Customer',
        })
        cls.other_partner = cls.env['res.partner'].create({
            'name': 'Test Merge Other Customer',
        })
        cls.product_a = cls.env['product.product'].create({
            'name': 'Test Merge Product A',
            'is_storable': True,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Test Merge Product B',
            'is_storable': True,
        })
        quant_model = cls.env['stock.quant']
        quant_model._update_available_quantity(
            cls.product_a, cls.stock_location, 100.0)
        quant_model._update_available_quantity(
            cls.product_b, cls.stock_location, 100.0)

    def _create_delivery(self, product, qty, partner=None, confirm=True):
        """Create a delivery of the given product, reserved by default."""
        partner = self.partner if partner is None else partner
        picking = self.env['stock.picking'].create({
            'partner_id': partner.id,
            'picking_type_id': self.warehouse.out_type_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'move_ids': [Command.create({
                'product_id': product.id,
                'product_uom_qty': qty,
                'location_id': self.stock_location.id,
                'location_dest_id': self.customer_location.id,
            })],
        })
        if confirm:
            picking.action_confirm()
            picking.action_assign()
        return picking

    def _create_receipt(self, product, qty):
        """Create and confirm a receipt of the given product."""
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.warehouse.in_type_id.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'move_ids': [Command.create({
                'product_id': product.id,
                'product_uom_qty': qty,
                'location_id': self.supplier_location.id,
                'location_dest_id': self.stock_location.id,
            })],
        })
        picking.action_confirm()
        return picking

    def _merge(self, pickings, existing=None):
        """Merge the pickings through the wizard."""
        wizard = self.env['merge.picking'].create({
            'merge_picking_ids': [Command.set(pickings.ids)],
            'existing_pick_id': existing.id if existing else False,
        })
        wizard.action_merge()
        return wizard

    def _get_merged_picking(self):
        """Return the picking created by the last merge."""
        return self.env['stock.picking'].search(
            [('origin', '=like', 'Merged (%')], order='id desc', limit=1)

    def test_01_list_action_is_bound(self):
        """Verify the merge action is available in the transfers list."""
        action = self.env.ref('merge_picking_orders.merge_picking_action')
        self.assertEqual(action.binding_model_id.model, 'stock.picking')
        self.assertEqual(action.binding_view_types, 'list')
        self.assertEqual(action.state, 'code')

    def test_02_action_opens_wizard(self):
        """Verify the action opens the wizard with the selected pickings."""
        pickings = (self._create_delivery(self.product_a, 2.0)
                    | self._create_delivery(self.product_b, 3.0))
        action = pickings.action_merge_picking()
        self.assertEqual(action['res_model'], 'merge.picking')
        self.assertEqual(action['target'], 'new')
        wizard = self.env['merge.picking'].browse(action['res_id'])
        self.assertEqual(wizard.merge_picking_ids, pickings)

    def test_03_merge_into_new_picking(self):
        """Verify merging creates a new ready picking holding all the moves
        and cancels the merged pickings.
        """
        first = self._create_delivery(self.product_a, 2.0)
        second = self._create_delivery(self.product_b, 3.0)
        self._merge(first | second)

        merged = self._get_merged_picking()
        self.assertNotIn(merged, first | second)
        self.assertEqual(merged.origin,
                         f'Merged ({first.name}, {second.name})')
        self.assertEqual(merged.partner_id, self.partner)
        self.assertEqual(merged.picking_type_id, self.warehouse.out_type_id)
        self.assertEqual(merged.state, 'assigned')
        self.assertEqual(
            sorted(merged.move_ids.mapped(
                lambda m: (m.product_id.id, m.product_uom_qty))),
            sorted([(self.product_a.id, 2.0), (self.product_b.id, 3.0)]))
        self.assertEqual((first | second).mapped('state'),
                         ['cancel', 'cancel'])

    def test_04_merge_into_existing_picking(self):
        """Verify merging into an existing picking moves the other pickings
        lines into it.
        """
        first = self._create_delivery(self.product_a, 2.0)
        second = self._create_delivery(self.product_b, 3.0)
        self._merge(first | second, existing=first)

        self.assertEqual(first.origin,
                         f'Merged ({first.name}, {second.name})')
        self.assertEqual(first.state, 'assigned')
        self.assertEqual(first.move_ids.product_id,
                         self.product_a | self.product_b)
        self.assertEqual(second.state, 'cancel')
        self.assertFalse(self._get_merged_picking() - first)

    def test_05_merged_picking_can_be_validated(self):
        """Verify the merged picking can be validated and delivers stock."""
        first = self._create_delivery(self.product_a, 2.0)
        second = self._create_delivery(self.product_a, 5.0)
        self._merge(first | second)
        merged = self._get_merged_picking()
        for move in merged.move_ids:
            move.quantity = move.product_uom_qty
        merged.move_ids.picked = True
        merged.button_validate()
        self.assertEqual(merged.state, 'done')
        self.assertEqual(self.product_a.qty_available, 93.0)

    def test_06_merge_draft_pickings(self):
        """Verify draft pickings can be merged and the result is confirmed."""
        first = self._create_delivery(self.product_a, 1.0, confirm=False)
        second = self._create_delivery(self.product_b, 1.0, confirm=False)
        self.assertEqual((first | second).mapped('state'),
                         ['draft', 'draft'])
        self._merge(first | second)
        merged = self._get_merged_picking()
        self.assertIn(merged.state, ('confirmed', 'assigned'))
        self.assertEqual(len(merged.move_ids), 2)

    def test_07_merge_receipts(self):
        """Verify receipts of the same partner can be merged."""
        first = self._create_receipt(self.product_a, 4.0)
        second = self._create_receipt(self.product_b, 6.0)
        self._merge(first | second)
        merged = self._get_merged_picking()
        self.assertEqual(merged.picking_type_id, self.warehouse.in_type_id)
        self.assertEqual(sum(merged.move_ids.mapped('product_uom_qty')), 10.0)

    def test_08_single_or_no_picking_not_allowed(self):
        """Verify one picking, or none, can not be merged."""
        picking = self._create_delivery(self.product_a, 1.0)
        with self.assertRaises(UserError):
            self._merge(picking)
        with self.assertRaises(UserError):
            self._merge(self.env['stock.picking'])

    def test_09_different_partners_not_allowed(self):
        """Verify pickings of different partners can not be merged, and a
        picking without partner is not merged with one that has a partner.
        """
        first = self._create_delivery(self.product_a, 1.0)
        other = self._create_delivery(
            self.product_b, 1.0, partner=self.other_partner)
        with self.assertRaises(UserError):
            self._merge(first | other)
        no_partner = self._create_delivery(
            self.product_b, 1.0, partner=self.env['res.partner'])
        with self.assertRaises(UserError):
            self._merge(first | no_partner)

    def test_10_different_types_not_allowed(self):
        """Verify a delivery and a receipt can not be merged."""
        delivery = self._create_delivery(self.product_a, 1.0)
        receipt = self._create_receipt(self.product_b, 1.0)
        with self.assertRaises(UserError):
            self._merge(delivery | receipt)

    def test_11_done_or_cancelled_not_allowed(self):
        """Verify done or cancelled pickings can not be merged."""
        first = self._create_delivery(self.product_a, 1.0)
        second = self._create_delivery(self.product_b, 1.0)
        second.action_cancel()
        with self.assertRaises(UserError):
            self._merge(first | second)
        self.assertEqual(first.state, 'assigned')

    def test_12_different_states_not_allowed(self):
        """Verify pickings in different states can not be merged."""
        ready = self._create_delivery(self.product_a, 1.0)
        draft = self._create_delivery(self.product_b, 1.0, confirm=False)
        with self.assertRaises(UserError):
            self._merge(ready | draft)

    def test_13_existing_picking_must_be_selected(self):
        """Verify the picking to merge into must be one of the selection."""
        first = self._create_delivery(self.product_a, 1.0)
        second = self._create_delivery(self.product_b, 1.0)
        outsider = self._create_delivery(self.product_b, 1.0)
        with self.assertRaises(UserError):
            self._merge(first | second, existing=outsider)
        self.assertEqual(outsider.state, 'assigned')

    def test_14_wizard_view_loads(self):
        """Verify the wizard form view loads with its fields and button."""
        arch = self.env['merge.picking'].get_view(
            view_id=self.env.ref(
                'merge_picking_orders.merge_picking_view_form').id)['arch']
        for name in ('merge_picking_ids', 'existing_pick_id', 'action_merge'):
            self.assertIn(name, arch)

    def test_15_stock_user_can_merge(self):
        """Verify an inventory user can merge pickings."""
        user = new_test_user(
            self.env, login='merge_picking_stock_user',
            groups='base.group_user,stock.group_stock_user')
        first = self._create_delivery(self.product_a, 1.0)
        second = self._create_delivery(self.product_b, 1.0)
        action = (first | second).with_user(user).action_merge_picking()
        self.env['merge.picking'].with_user(user).browse(
            action['res_id']).action_merge()
        self.assertEqual((first | second).mapped('state'),
                         ['cancel', 'cancel'])
