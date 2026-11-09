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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCustomerSoHistory(TransactionCase):
    """Tests for the customer sale order history tab."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create(
            {'name': 'History Customer'})
        cls.other_partner = cls.env['res.partner'].create(
            {'name': 'Other Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'History Product',
            'list_price': 50.0,
        })
        cls.confirmed_order = cls._create_order(cls.partner, 3.0, 40.0)
        cls.confirmed_order.action_confirm()
        cls.draft_order = cls._create_order(cls.partner, 7.0, 10.0)
        cls.other_order = cls._create_order(cls.other_partner, 1.0, 5.0)
        cls.other_order.action_confirm()

    @classmethod
    def _create_order(cls, partner, qty, price):
        return cls.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': qty,
                'price_unit': price,
            })],
        })

    def test_history_loads_confirmed_orders_only(self):
        """Only confirmed lines of the selected customer are loaded."""
        order = self.env['sale.order'].new({'partner_id': self.partner.id})
        order._onchange_partner_id_order_history()
        history = order.order_details_ids
        self.assertEqual(len(history), 1)
        self.assertEqual(history.name, self.confirmed_order.name)
        self.assertEqual(history.product_id, self.product)
        self.assertEqual(history.product_uom_qty, 3.0)
        self.assertEqual(history.price_unit, 40.0)
        self.assertEqual(
            history.price_subtotal,
            self.confirmed_order.order_line.price_subtotal)

    def test_history_cleared_without_customer(self):
        """The history is emptied when the customer is removed."""
        order = self.env['sale.order'].new({'partner_id': self.partner.id})
        order._onchange_partner_id_order_history()
        self.assertTrue(order.order_details_ids)
        order.partner_id = False
        order._onchange_partner_id_order_history()
        self.assertFalse(order.order_details_ids)

    def test_history_empty_for_new_customer(self):
        """A customer without confirmed orders gets no history."""
        new_partner = self.env['res.partner'].create({'name': 'No History'})
        order = self.env['sale.order'].new({'partner_id': new_partner.id})
        order._onchange_partner_id_order_history()
        self.assertFalse(order.order_details_ids)

    def test_action_add_creates_order_line(self):
        """The Add button copies the history line to the order lines."""
        target = self.env['sale.order'].create({'partner_id': self.partner.id})
        history_line = self.env['order.history.line'].create({
            'order_id': target.id,
            'name': self.confirmed_order.name,
            'product_id': self.product.id,
            'product_uom_qty': 3.0,
            'price_unit': 40.0,
            'price_subtotal': 120.0,
        })
        history_line.action_add()
        self.assertEqual(len(target.order_line), 1)
        line = target.order_line
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.product_uom_qty, 3.0)
        self.assertEqual(line.price_unit, 40.0)

    def test_action_add_does_not_change_original_order(self):
        """Adding a history line leaves the original order untouched."""
        target = self.env['sale.order'].create({'partner_id': self.partner.id})
        history_line = self.env['order.history.line'].create({
            'order_id': target.id,
            'product_id': self.product.id,
            'product_uom_qty': 2.0,
            'price_unit': 40.0,
        })
        history_line.action_add()
        self.assertEqual(len(self.confirmed_order.order_line), 1)
        self.assertEqual(self.confirmed_order.order_line.product_uom_qty, 3.0)
