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
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestTableReservation(TransactionCase):
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
        cls.booking_pos_product = cls.env.ref(
            "table_reservation_on_website.product_product_table_booking_pos"
        )

    def _create_reservation(self, **vals):
        defaults = {
            "customer_id": self.partner.id,
            "floor_id": self.floor.id,
            "booked_tables_ids": [(6, 0, self.table_1.ids)],
            "date": self.future_date,
            "starting_at": "10:00",
            "ending_at": "12:00",
            "state": "draft",
        }
        defaults.update(vals)
        return self.env["table.reservation"].create(defaults)

    def test_create_assigns_sequence(self):
        reservation = self._create_reservation()

        self.assertNotEqual(reservation.sequence, "New")
        self.assertTrue(reservation.sequence.startswith("TR"))

    def test_onchange_time_rejects_invalid_format(self):
        reservation = self.env["table.reservation"].new({
            "floor_id": self.floor.id,
            "date": self.future_date,
            "starting_at": "25:00",
            "ending_at": "12:00",
        })

        with self.assertRaises(UserError):
            reservation._onchange_time()

    def test_compute_available_tables_excludes_overlapping_reserved_tables(self):
        self._create_reservation(
            booked_tables_ids=[(6, 0, self.table_1.ids)],
            state="reserved",
            starting_at="10:00",
            ending_at="12:00",
        )
        reservation = self.env["table.reservation"].new({
            "floor_id": self.floor.id,
            "date": self.future_date,
            "starting_at": "11:00",
            "ending_at": "13:00",
        })

        reservation._compute_available_tables()

        self.assertNotIn(self.table_1.id, reservation.available_tables.ids)
        self.assertIn(self.table_2.id, reservation.available_tables.ids)

    def test_compute_booking_amount_sums_table_rates_when_charge_enabled(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "table_reservation_on_website.reservation_charge", True
        )
        reservation = self._create_reservation(
            booked_tables_ids=[(6, 0, (self.table_1 | self.table_2).ids)]
        )
        reservation._compute_booking_amount()

        self.assertEqual(reservation.booking_amount, 30.0)

    def test_state_actions_update_status(self):
        reservation = self._create_reservation()
        reservation.action_reserved()
        self.assertEqual(reservation.state, "reserved")
        reservation.action_done()
        self.assertEqual(reservation.state, "done")
        reservation.action_cancel()
        self.assertEqual(reservation.state, "cancel")

    def test_table_reservations_returns_future_reserved_records(self):
        reservation = self._create_reservation(state="reserved")

        data = self.env["table.reservation"].table_reservations()

        self.assertIn(reservation.id, [record["id"] for record in data])

    def test_past_date_constraint_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self._create_reservation(date=fields.Date.today() - timedelta(days=1))

    def test_get_reservation_amount_returns_sum_of_table_rates(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "table_reservation_on_website.reservation_charge", True
        )

        amount = self.env["table.reservation"].get_reservation_amount(
            f"{self.table_1.id},{self.table_2.id}"
        )

        self.assertEqual(amount, 30.0)

    def test_create_table_reservation_creates_reserved_pos_booking(self):
        product_id = self.env["table.reservation"].create_table_reservation(
            table_id=f"{self.table_1.id},{self.table_2.id}",
            date=self.future_date.strftime("%Y-%m-%d"),
            start_time="14:00",
            end_time="16:00",
            partner=str(self.partner.id),
            lead_time="01:30",
            floor_id=self.floor.id,
            order_name="POS/001",
        )

        reservation = self.env["table.reservation"].search(
            [("order_name", "=", "POS/001")], limit=1
        )
        self.assertEqual(product_id, self.booking_pos_product.id)
        self.assertEqual(reservation.state, "reserved")
        self.assertEqual(reservation.type, "pos")
        self.assertEqual(reservation.booked_tables_ids, self.table_1 | self.table_2)

    def test_get_table_details_returns_only_available_tables(self):
        self._create_reservation(
            booked_tables_ids=[(6, 0, self.table_1.ids)],
            state="reserved",
            starting_at="10:00",
            ending_at="12:00",
            lead_time=0.0,
        )

        result = self.env["table.reservation"].get_table_details(
            floor_id=self.floor.id,
            date=self.future_date.strftime("%Y-%m-%d"),
            start_time="11:00",
            end_time="12:30",
        )

        self.assertEqual(result, [{"id": self.table_2.id, "name": self.table_2.table_number}])

    def test_get_avail_table_returns_false_for_overlapping_reserved_booking(self):
        self._create_reservation(
            booked_tables_ids=[(6, 0, self.table_1.ids)],
            state="reserved",
            starting_at="10:00",
            ending_at="12:00",
            lead_time=0.0,
        )

        available = self.env["table.reservation"].get_avail_table(
            floor_id=self.floor.id,
            date=self.future_date.strftime("%Y-%m-%d"),
            start_time="11:00",
            end_time="11:30",
            table_ids=str(self.table_1.id),
        )

        self.assertFalse(available)

    def test_edit_reservations_updates_booking_and_returns_pos_product(self):
        reservation = self._create_reservation(order_name="POS/OLD")

        product_id = self.env["table.reservation"].edit_reservations(
            booking_id=reservation.id,
            date=self.future_date.strftime("%Y-%m-%d"),
            customer=str(self.partner.id),
            start_time="13:00",
            end_time="15:00",
            floor=self.floor.id,
            table_ids=[self.table_2.id],
            lead=1.0,
            order_name="POS/EDIT",
        )

        self.assertEqual(product_id, self.booking_pos_product.id)
        self.assertEqual(reservation.order_name, "POS/EDIT")
        self.assertEqual(reservation.booked_tables_ids, self.table_2)

    def test_add_payment_returns_pos_product_and_selected_table_rate(self):
        result = self.env["table.reservation"].add_payment(
            table_id=self.table_2.id,
            floor_id=self.floor.id,
        )

        self.assertEqual(result["product"], self.booking_pos_product.id)
        self.assertEqual(result["rate"], self.table_2.rate)

    def test_get_table_details_enforces_lead_time_constraint(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "table_reservation_on_website.is_lead_time", True
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "table_reservation_on_website.reservation_lead_time", 1.0
        )
        today_str = fields.Date.today().strftime("%Y-%m-%d")
        tables = self.env["table.reservation"].get_table_details(
            floor_id=self.floor.id,
            date=today_str,
            start_time="00:00",
            end_time="01:00",
        )
        self.assertEqual(tables, [])

