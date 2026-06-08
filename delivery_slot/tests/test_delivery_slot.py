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


class TestDeliverySlot(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Delivery Slot Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Delivery Slot Product',
            'type': 'service',
            'list_price': 10.0,
        })
        cls.home_slot = cls.env['slot.time'].create({
            'name': 'Morning Home Slot',
            'slot_type': 'home',
            'time_from': '8',
            'time_to': '10',
        })
        cls.office_slot = cls.env['slot.time'].create({
            'name': 'Office Slot',
            'slot_type': 'office',
            'time_from': '10',
            'time_to': '12',
        })
        cls.delivery_date = Date.to_date('2026-06-15')
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'slot_per_product': True,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 10.0,
                'delivery_date': cls.delivery_date,
                'slot_id': cls.home_slot.id,
            })],
        })

    def test_delivery_ids_are_computed_from_matching_sale_order_lines(self):
        delivery_slot = self.env['delivery.slot'].create({
            'delivery_date': self.delivery_date,
            'slot_id': self.home_slot.id,
            'delivery_limit': 2,
        })

        self.assertIn(self.sale_order, delivery_slot.delivery_ids)
        self.assertEqual(delivery_slot.total_delivery, 1)
        self.assertEqual(delivery_slot.remaining_slots, 1)
        self.assertTrue(delivery_slot.active)

    def test_remaining_slots_deactivates_full_slot(self):
        delivery_slot = self.env['delivery.slot'].create({
            'delivery_date': self.delivery_date,
            'slot_id': self.home_slot.id,
            'delivery_limit': 1,
        })

        self.assertEqual(delivery_slot.remaining_slots, 0)
        self.assertFalse(delivery_slot.active)

    def test_write_refreshes_related_sale_orders(self):
        delivery_slot = self.env['delivery.slot'].create({
            'delivery_date': self.delivery_date,
            'slot_id': self.home_slot.id,
        })
        self.assertIn(self.sale_order, delivery_slot.delivery_ids)

        delivery_slot.write({'slot_id': self.office_slot.id})

        self.assertNotIn(self.sale_order, delivery_slot.delivery_ids)
