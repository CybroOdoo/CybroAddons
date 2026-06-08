# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.fields import Command, Date
from odoo.tests.common import TransactionCase


class TestSaleOrderDeliverySlot(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Sale Slot Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Sale Slot Product',
            'type': 'service',
            'list_price': 25.0,
        })
        cls.slot = cls.env['slot.time'].create({
            'name': 'Sale Order Slot',
            'slot_type': 'home',
            'time_from': '9',
            'time_to': '11',
        })
        cls.delivery_date = Date.to_date('2026-06-16')

    def _create_order(self, slot_per_product=True):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'slot_per_product': slot_per_product,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 25.0,
                'delivery_date': self.delivery_date,
                'slot_id': self.slot.id,
            })],
        })

    def test_action_confirm_creates_delivery_slot_for_order_line(self):
        order = self._create_order()

        order.action_confirm()

        delivery_slot = self.env['delivery.slot'].search([
            ('delivery_date', '=', self.delivery_date),
            ('slot_id', '=', self.slot.id),
        ])
        self.assertEqual(len(delivery_slot), 1)
        self.assertIn(order, delivery_slot.delivery_ids)

    def test_delivery_slot_count_uses_matching_active_slots(self):
        order = self._create_order()
        self.env['delivery.slot'].create({
            'delivery_date': self.delivery_date,
            'slot_id': self.slot.id,
        })

        order._compute_delivery_slot_count()

        self.assertEqual(order.slot_count, 1)

    def test_delivery_slot_count_is_zero_when_feature_disabled(self):
        order = self._create_order(slot_per_product=False)
        self.env['delivery.slot'].create({
            'delivery_date': self.delivery_date,
            'slot_id': self.slot.id,
        })

        order._compute_delivery_slot_count()

        self.assertEqual(order.slot_count, 0)

    def test_action_view_delivery_slot_returns_matching_slot_domain(self):
        order = self._create_order()
        delivery_slot = self.env['delivery.slot'].create({
            'delivery_date': self.delivery_date,
            'slot_id': self.slot.id,
        })

        action = order.action_view_delivery_slot()

        self.assertEqual(action['res_model'], 'delivery.slot')
        self.assertIn(('id', 'in', [delivery_slot.id]), action['domain'])
