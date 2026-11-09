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
"""Tests for the Merge RFQ wizard."""
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMergeRfq(TransactionCase):
    """Cover every merge type of the merge.rfq wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env['res.partner'].create({'name': 'Merge Vendor'})
        cls.new_vendor = cls.env['res.partner'].create(
            {'name': 'New Merge Vendor'})
        cls.product_a = cls.env['product.product'].create(
            {'name': 'Merge Product A', 'purchase_ok': True})
        cls.product_b = cls.env['product.product'].create(
            {'name': 'Merge Product B', 'purchase_ok': True})

    def _create_order(self, lines):
        """Create an RFQ with (product, qty, price) lines."""
        return self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_qty': qty,
                'price_unit': price,
            }) for product, qty, price in lines],
        })

    def _create_orders(self):
        """Two RFQs sharing one product/price pair and one distinct price."""
        po_1 = self._create_order([
            (self.product_a, 2.0, 10.0),
            (self.product_b, 1.0, 5.0),
        ])
        po_2 = self._create_order([
            (self.product_a, 3.0, 10.0),
            (self.product_a, 1.0, 20.0),
        ])
        return po_1 | po_2

    def _run_wizard(self, orders, merge_type, **values):
        """Open the wizard on the given orders and run the merge."""
        wizard = self.env['merge.rfq'].with_context(
            active_ids=orders.ids).create({
                'merge_type': merge_type,
                'purchase_order_ids': [(6, 0, orders.ids)],
                **values,
            })
        wizard.action_merge_orders()
        return wizard

    def _line_summary(self, order):
        """Return sorted (product, price, qty) tuples of an order."""
        return sorted(
            (line.product_id.id, line.price_unit, line.product_qty)
            for line in order.order_line)

    def _expected_summary(self):
        """Lines expected after merging the orders of _create_orders."""
        return sorted([
            (self.product_a.id, 10.0, 5.0),
            (self.product_b.id, 5.0, 1.0),
            (self.product_a.id, 20.0, 1.0),
        ])

    def _find_new_order(self, existing):
        """Return the order created by the wizard."""
        return self.env['purchase.order'].search(
            [('partner_id', '=', self.new_vendor.id),
             ('id', 'not in', existing.ids)])

    def test_merge_needs_two_orders(self):
        """Selecting a single RFQ raises an error."""
        order = self._create_order([(self.product_a, 1.0, 10.0)])
        with self.assertRaises(UserError):
            self._run_wizard(order, 'cancel_and_new',
                             partner_id=self.new_vendor.id)

    def test_merge_rejects_confirmed_orders(self):
        """Orders outside the RFQ / RFQ sent state cannot be merged."""
        orders = self._create_orders()
        orders[0].button_confirm()
        with self.assertRaises(UserError):
            self._run_wizard(orders, 'cancel_and_new',
                             partner_id=self.new_vendor.id)

    def test_cancel_and_new(self):
        """A new RFQ gets all lines and the selected RFQs are cancelled."""
        orders = self._create_orders()
        orders[1].write({'state': 'sent'})
        self._run_wizard(orders, 'cancel_and_new',
                         partner_id=self.new_vendor.id)
        new_order = self._find_new_order(orders)
        self.assertEqual(len(new_order), 1)
        self.assertEqual(self._line_summary(new_order),
                         self._expected_summary())
        self.assertEqual(set(orders.mapped('state')), {'cancel'})

    def test_delete_and_new(self):
        """A new RFQ gets all lines and the selected RFQs are deleted."""
        orders = self._create_orders()
        self._run_wizard(orders, 'delete_and_new',
                         partner_id=self.new_vendor.id)
        new_order = self._find_new_order(orders)
        self.assertEqual(self._line_summary(new_order),
                         self._expected_summary())
        self.assertFalse(orders.exists())

    def test_cancel_and_merge(self):
        """Lines move into the chosen RFQ and the others are cancelled."""
        orders = self._create_orders()
        target, other = orders[0], orders[1]
        self._run_wizard(orders, 'cancel_and_merge',
                         purchase_order_id=target.id)
        self.assertEqual(self._line_summary(target),
                         self._expected_summary())
        self.assertEqual(target.state, 'draft')
        self.assertEqual(other.state, 'cancel')

    def test_delete_and_merge(self):
        """Lines move into the chosen RFQ and the others are deleted."""
        orders = self._create_orders()
        target, other = orders[0], orders[1]
        self._run_wizard(orders, 'delete_and_merge',
                         purchase_order_id=target.id)
        self.assertEqual(self._line_summary(target),
                         self._expected_summary())
        self.assertTrue(target.exists())
        self.assertFalse(other.exists())

    def test_merge_into_empty_order(self):
        """Merging into an RFQ without lines copies every line."""
        target = self._create_order([])
        other = self._create_order([(self.product_a, 2.0, 10.0)])
        self._run_wizard(target | other, 'cancel_and_merge',
                         purchase_order_id=target.id)
        self.assertEqual(self._line_summary(target),
                         [(self.product_a.id, 10.0, 2.0)])
        self.assertEqual(other.state, 'cancel')
