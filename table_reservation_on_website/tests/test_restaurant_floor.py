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


class TestRestaurantFloor(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        pos_config = cls.env["pos.config"].create({
            "name": "Website Reservation POS",
            "module_pos_restaurant": True,
        })
        cls.floor = cls.env["restaurant.floor"].create({
            "name": "Main Floor",
            "pos_config_ids": [(6, 0, pos_config.ids)],
        })

    def test_compute_is_show_field_depends_on_reservation_charge_param(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("table_reservation_on_website.reservation_charge", True)
        self.floor._compute_is_show_field()
        self.assertTrue(self.floor.is_show_field)

        params.set_param("table_reservation_on_website.reservation_charge", False)
        self.floor._compute_is_show_field()
        self.assertFalse(self.floor.is_show_field)
