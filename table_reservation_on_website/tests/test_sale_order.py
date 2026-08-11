# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Reservation Customer"})
        pos_config = cls.env["pos.config"].create({
            "name": "Website Reservation POS",
            "module_pos_restaurant": True,
        })
        cls.floor = cls.env["restaurant.floor"].create({
            "name": "Main Floor",
            "pos_config_ids": [(6, 0, pos_config.ids)],
        })
        cls.table_1 = cls.env["restaurant.table"].create({
            "floor_id": cls.floor.id,
            "table_number": 1,
            "seats": 4,
            "rate": 10.0,
        })
        cls.table_2 = cls.env["restaurant.table"].create({
            "floor_id": cls.floor.id,
            "table_number": 2,
            "seats": 4,
            "rate": 20.0,
        })
        cls.future_date = fields.Date.today() + timedelta(days=1)
        cls.reservation = cls.env["table.reservation"].create({
            "customer_id": cls.partner.id,
            "floor_id": cls.floor.id,
            "booked_tables_ids": [(6, 0, cls.table_1.ids)],
            "date": cls.future_date,
            "starting_at": "10:00",
            "ending_at": "12:00",
            "state": "draft",
        })

    def test_sale_order_stores_reservation_fields(self):
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "table_reservation_id": self.reservation.id,
            "tables_ids": [(6, 0, (self.table_1 | self.table_2).ids)],
            "floors": self.floor.id,
            "date": self.future_date,
            "starting_at": "10:00",
            "ending_at": "12:00",
            "booking_amount": 30.0,
        })

        self.assertEqual(order.table_reservation_id, self.reservation)
        self.assertEqual(order.tables_ids, self.table_1 | self.table_2)
        self.assertEqual(order.floors, self.floor.id)
        self.assertEqual(order.booking_amount, 30.0)
