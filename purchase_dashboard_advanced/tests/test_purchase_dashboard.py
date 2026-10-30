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

from datetime import timedelta

from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPurchaseDashboard(TransactionCase):
    """Tests for the data methods feeding the advanced purchase dashboard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.categ = cls.env['product.category'].create({'name': 'Dash Categ'})
        cls.product = cls.env['product.product'].create({
            'name': 'Dash Product',
            'categ_id': cls.categ.id,
        })
        cls.vendor = cls.env['res.partner'].create({'name': 'Dash Vendor'})
        now = fields.Datetime.now()
        cls.order = cls._create_order(cls.vendor, now, now, '1')
        cls.order.button_confirm()
        cls.pending_order = cls._create_order(
            cls.vendor, now, now - timedelta(days=5), '0')
        cls.pending_order.button_confirm()
        cls.upcoming_order = cls._create_order(
            cls.vendor, now, now + timedelta(days=5), '0')
        cls.upcoming_order.button_confirm()
        cls.draft_order = cls._create_order(cls.vendor, now, now, '0')
        cls.cancel_order = cls._create_order(cls.vendor, now, now, '0')
        cls.cancel_order.button_cancel()
        cls.env.flush_all()

    @classmethod
    def _create_order(cls, vendor, date_order, date_planned, priority):
        return cls.env['purchase.order'].create({
            'partner_id': vendor.id,
            'date_order': date_order,
            'priority': priority,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_qty': 5,
                'price_unit': 10,
                'date_planned': date_planned,
            })],
        })

    def test_purchase_data(self):
        """Tile data counts confirmed orders, priority orders and vendors."""
        data = self.env['purchase.order'].get_purchase_data()
        self.assertGreaterEqual(data['purchase_orders'], 3)
        self.assertGreaterEqual(data['priority_orders'], 1)
        self.assertGreaterEqual(data['vendors'], 1)
        self.assertGreater(data['purchase_amount'], 0)

    def test_period_data(self):
        """Each filter returns the dashboard keys and sees the new order."""
        purchase = self.env['purchase.order']
        for mode in ('this_year', 'this_month', 'this_week', 'today'):
            data = purchase.get_select_mode_data(mode)
            self.assertGreaterEqual(data['purchase_orders'], 3, mode)
            self.assertGreaterEqual(data['priority_orders'], 1, mode)
            self.assertGreaterEqual(data['vendors'], 1, mode)
            self.assertIn(self.order.id, data['order_ids'], mode)
            self.assertIn(self.vendor.id, data['vendor_id'], mode)
        self.assertFalse(purchase.get_select_mode_data('unknown'))

    def test_top_chart_data(self):
        """Top products, vendors and sales representatives are returned."""
        purchase = self.env['purchase.order']
        counts, names = purchase.get_top_chart_data('top_product')
        self.assertIn('Dash Product', names)
        self.assertEqual(len(counts), len(names))
        counts, names = purchase.get_top_chart_data('top_vendor')
        self.assertIn('Dash Vendor', names)
        counts, names = purchase.get_top_chart_data('top_rep')
        self.assertTrue(names)
        self.assertEqual(purchase.get_top_chart_data('unknown'), [])

    def test_orders_by_month(self):
        """Orders by month always cover the twelve months."""
        data = self.env['purchase.order'].get_orders_by_month()
        self.assertEqual(len(data['count']), 12)
        self.assertEqual(len(data['dates']), 12)
        self.assertGreaterEqual(sum(data['count']), 3)

    def test_vendors_and_vendor_details(self):
        """Vendor list and per vendor details are returned."""
        purchase = self.env['purchase.order']
        vendors = purchase.purchase_vendors()
        self.assertIn(self.vendor.id, [rec['id'] for rec in vendors])
        details = purchase.purchase_vendor_details(self.vendor.id)
        self.assertEqual(len(details['dates']), 12)
        self.assertEqual(len(details['po_count']), 12)
        self.assertGreater(sum(details['purchase_amount']), 0)
        self.assertGreaterEqual(sum(details['draft_count']), 1)
        self.assertGreaterEqual(sum(details['cancel_count']), 1)
        self.assertTrue(purchase.purchase_vendor_details(False))

    def test_pending_and_upcoming(self):
        """Late and coming orders are listed with their vendor."""
        purchase = self.env['purchase.order']
        pending = purchase.get_pending_purchase_data()
        self.assertIn(self.pending_order.name, pending['order'])
        self.assertIn('Dash Vendor', pending['vendor'])
        upcoming = purchase.get_upcoming_purchase_data()
        self.assertIn(self.upcoming_order.name, upcoming['order'])
        index = upcoming['order'].index(self.upcoming_order.name)
        self.assertEqual(upcoming['state'][index], 'Purchase Order')

    def test_product_category_analysis(self):
        """Product category analysis and drill down are returned."""
        line = self.env['purchase.order.line']
        data = line.product_categ_analysis()
        self.assertIn('Dash Product', data['values']['name'])
        self.assertIn(self.categ.id, [cat[0] for cat in data['category_id']])
        detail = line.product_categ_data(self.categ.id)
        self.assertIn('Dash Product', detail['name'])
        self.assertEqual(len(detail['name']), len(detail['count']))
        self.assertIn('name', line.product_categ_data(False))
