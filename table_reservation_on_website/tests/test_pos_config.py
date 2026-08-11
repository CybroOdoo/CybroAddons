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


class TestPosConfig(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env["pos.config"].create({
            "name": "Website Reservation POS",
            "module_pos_restaurant": True,
        })

    def test_compute_flags_and_hours_from_config_parameters(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("table_reservation_on_website.is_lead_time", True)
        params.set_param("table_reservation_on_website.reservation_charge", True)
        params.set_param("table_reservation_on_website.opening_hour", 8.5)
        params.set_param("table_reservation_on_website.closing_hour", 22.0)

        self.pos_config._compute_has_lead_time()
        self.pos_config._compute_has_reservation_charge()
        self.pos_config._compute_opening_hour()
        self.pos_config._compute_closing_hour()

        self.assertTrue(self.pos_config.has_lead_time)
        self.assertTrue(self.pos_config.has_reservation_charge)
        self.assertEqual(self.pos_config.opening_hour, 8.5)
        self.assertEqual(self.pos_config.closing_hour, 22.0)
