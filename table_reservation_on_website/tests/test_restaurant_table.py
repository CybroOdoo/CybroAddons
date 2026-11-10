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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for restaurant.table table reservation fields and computes."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRestaurantTable(TransactionCase):
    """Test restaurant.table computes and rate field."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.floor = cls.env['restaurant.floor'].create({
            'name': 'Terrace Floor',
        })
        cls.table = cls.env['restaurant.table'].create({
            'table_number': 101,
            'floor_id': cls.floor.id,
            'seats': 4,
            'rate': 50.0,
        })

    def test_compute_is_show_field(self):
        """Test _compute_is_show_field depending on reservation_charge parameter."""
        param_obj = self.env['ir.config_parameter'].sudo()

        param_obj.set_bool('table_reservation_on_website.reservation_charge', True)
        self.table._compute_is_show_field()
        self.assertTrue(self.table.is_show_field)

        param_obj.set_bool('table_reservation_on_website.reservation_charge', False)
        self.table._compute_is_show_field()
        self.assertFalse(self.table.is_show_field)

    def test_table_rate_and_seats(self):
        """Test rate and seats values on table."""
        self.assertEqual(self.table.seats, 4)
        self.assertAlmostEqual(self.table.rate, 50.0)
        self.table.write({'rate': 75.0})
        self.assertAlmostEqual(self.table.rate, 75.0)

