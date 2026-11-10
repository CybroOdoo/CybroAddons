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
"""Test suite for restaurant.floor table reservation field computes."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRestaurantFloor(TransactionCase):
    """Test restaurant.floor computes and functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.floor = cls.env['restaurant.floor'].create({
            'name': 'Main Dining Floor',
        })

    def test_compute_is_show_field(self):
        """Test _compute_is_show_field with reservation_charge active and inactive."""
        param_obj = self.env['ir.config_parameter'].sudo()

        param_obj.set_bool('table_reservation_on_website.reservation_charge', True)
        self.floor._compute_is_show_field()
        self.assertTrue(self.floor.is_show_field)

        param_obj.set_bool('table_reservation_on_website.reservation_charge', False)
        self.floor._compute_is_show_field()
        self.assertFalse(self.floor.is_show_field)

