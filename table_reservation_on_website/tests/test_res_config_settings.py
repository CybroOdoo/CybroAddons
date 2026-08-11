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
from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env["pos.config"].create({
            "name": "Website Reservation POS",
            "module_pos_restaurant": True,
        })

    def test_set_values_persists_reservation_parameters(self):
        settings = self.env["res.config.settings"].create({
            "pos_config_id": self.pos_config.id,
            "reservation_charge": True,
            "refund": "Refund note",
            "is_lead_time": True,
            "reservation_lead_time": 1.5,
            "pos_set_opening_hours": True,
            "pos_opening_hour": 9.0,
            "pos_closing_hour": 23.0,
        })

        settings.set_values()
        params = self.env["ir.config_parameter"].sudo()

        self.assertEqual(
            params.get_param("table_reservation_on_website.refund"),
            "Refund note",
        )
        self.assertEqual(
            params.get_param("table_reservation_on_website.is_lead_time"),
            "True",
        )
        self.assertEqual(
            params.get_param("table_reservation_on_website.reservation_lead_time"),
            "1.5",
        )
        self.assertTrue(self.pos_config.set_opening_hours)
        self.assertEqual(self.pos_config.opening_hour, 9.0)
        self.assertEqual(self.pos_config.closing_hour, 23.0)

    def test_get_values_reads_reservation_parameters(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("table_reservation_on_website.refund", "Policy note")
        params.set_param("table_reservation_on_website.is_lead_time", True)
        params.set_param("table_reservation_on_website.reservation_lead_time", 2.0)
        self.pos_config.write({
            "set_opening_hours": True,
            "opening_hour": 8.0,
            "closing_hour": 21.0,
        })

        values = self.env["res.config.settings"].create({
            "pos_config_id": self.pos_config.id,
        }).get_values()

        self.assertEqual(values["refund"], "Policy note")
        self.assertEqual(values["is_lead_time"], "True")
        self.assertEqual(values["reservation_lead_time"], "2.0")
        self.assertTrue(values["pos_set_opening_hours"])
        self.assertEqual(values["pos_opening_hour"], 8.0)
        self.assertEqual(values["pos_closing_hour"], 21.0)
