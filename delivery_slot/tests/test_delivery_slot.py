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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDeliverySlot(TransactionCase):
    """Tests for the delivery slot feature"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.slot_home = cls.env['slot.time'].create({
            'name': 'Morning', 'slot_type': 'home',
            'time_from': '6', 'time_to': '18'})
        cls.slot_office = cls.env['slot.time'].create({
            'name': 'Office', 'slot_type': 'office',
            'time_from': '9', 'time_to': '17'})
        cls.partner = cls.env['res.partner'].create({'name': 'Slot Customer'})
        cls.product_a = cls.env['product.product'].create(
            {'name': 'Slot Product A', 'type': 'consu'})
        cls.product_b = cls.env['product.product'].create(
            {'name': 'Slot Product B', 'type': 'consu'})
        cls.date = fields.Date.today()

    def _create_order(self, slot_per_product=True, products=None):
        products = products or self.product_a
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'slot_per_product': slot_per_product,
            'order_line': [Command.create({
                'product_id': product.id,
                'product_uom_qty': 1,
                'delivery_date': self.date,
                'slot_id': self.slot_home.id,
            }) for product in products],
        })

    def test_slot_time_selection(self):
        """Slot time stores the chosen hours"""
        self.assertEqual(self.slot_home.time_from, '6')
        labels = dict(self.env['slot.time']._fields['time_from'].selection)
        self.assertEqual(labels['0'], '12:00 AM')
        self.assertEqual(labels['13'], '1:00 PM')

    def test_default_slot_per_product(self):
        """The order default follows the configuration parameter"""
        settings = self.env['res.config.settings']
        settings.create({'enable_delivery_date': True}).execute()
        self.assertTrue(self.env['sale.order']._default_slot_per_product())
        settings.create({'enable_delivery_date': False}).execute()
        self.assertFalse(self.env['sale.order']._default_slot_per_product())

    def test_confirm_creates_delivery_slot(self):
        """Confirming an order creates and links the delivery slot"""
        order = self._create_order()
        order.action_confirm()
        delivery_slot = order.order_line.delivery_slot_id
        self.assertTrue(delivery_slot)
        self.assertEqual(delivery_slot.slot_id, self.slot_home)
        self.env.invalidate_all()
        self.assertEqual(delivery_slot.delivery_ids, order)
        self.assertEqual(delivery_slot.total_delivery, 1)
        self.assertEqual(delivery_slot.remaining_slots, 99)
        self.assertEqual(order.slot_count, 1)

    def test_second_order_reuses_slot(self):
        """Orders on the same date and slot share one delivery slot"""
        first = self._create_order()
        first.action_confirm()
        second = self._create_order()
        second.action_confirm()
        self.assertEqual(first.order_line.delivery_slot_id,
                         second.order_line.delivery_slot_id)
        self.env.invalidate_all()
        self.assertEqual(first.order_line.delivery_slot_id.total_delivery, 2)

    def test_slot_limit_reached(self):
        """A full slot has no remaining deliveries"""
        order = self._create_order()
        order.action_confirm()
        delivery_slot = order.order_line.delivery_slot_id
        delivery_slot.delivery_limit = 1
        self.env.invalidate_all()
        self.assertEqual(delivery_slot.remaining_slots, 0)

    def test_view_delivery_slot_action(self):
        """The smart button action only lists the order slots"""
        order = self._create_order()
        order.action_confirm()
        action = order.action_view_delivery_slot()
        self.assertEqual(action['res_model'], 'delivery.slot')
        self.assertEqual(action['domain'][0][2],
                         order.order_line.delivery_slot_id.ids)

    def test_order_without_slot_feature(self):
        """Orders without the feature keep the standard behaviour"""
        order = self._create_order(slot_per_product=False)
        order.action_confirm()
        self.assertFalse(order.order_line.delivery_slot_id)
        self.assertEqual(order.slot_count, 0)

    def test_picking_per_line(self):
        """One picking is created for every line when slots are enabled"""
        products = self.product_a | self.product_b
        slot_order = self._create_order(products=products)
        slot_order.action_confirm()
        self.assertEqual(len(slot_order.picking_ids), 2)
        plain_order = self._create_order(
            slot_per_product=False, products=products)
        plain_order.action_confirm()
        self.assertEqual(len(plain_order.picking_ids), 1)
