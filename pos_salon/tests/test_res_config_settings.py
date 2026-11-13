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
#############################################################################
from odoo.tests import tagged
from .common import TestSalonCommon


@tagged('post_install', '-at_install', 'pos_salon')
class TestResConfigSettings(TestSalonCommon):
    """Test suite for res.config.settings salon extensions."""

    __test__ = True

    def test_01_onchange_pos_is_salon_defaults(self):
        """Turning on pos_is_salon enables pos_show_appointments by default."""
        settings = self.env['res.config.settings'].new({
            'pos_config_id': self.pos_config.id,
            'pos_is_salon': True,
            'pos_show_appointments': False,
        })
        settings._onchange_pos_is_salon_defaults()
        self.assertTrue(settings.pos_show_appointments)

    def test_02_onchange_pos_show_appointments_disables_all(self):
        """Turning off pos_show_appointments clears pos_show_all_appointments."""
        settings = self.env['res.config.settings'].new({
            'pos_config_id': self.pos_config.id,
            'pos_show_appointments': False,
            'pos_show_all_appointments': True,
        })
        settings._onchange_pos_show_appointments()
        self.assertFalse(settings.pos_show_all_appointments)

    def test_03_onchange_pos_salon_restaurant_conflict_existing_salon(self):
        """When config is already salon, enabling bar/restaurant resets restaurant and warns."""
        self.pos_config.is_salon = True
        settings = self.env['res.config.settings'].new({
            'pos_config_id': self.pos_config.id,
            'pos_is_salon': True,
            'pos_module_pos_restaurant': True,
        })
        res = settings._onchange_pos_salon_restaurant()
        self.assertFalse(settings.pos_module_pos_restaurant)
        self.assertIn('warning', res)
        self.assertEqual(res['warning']['title'], 'Not allowed')

    def test_04_onchange_pos_salon_restaurant_conflict_existing_restaurant(self):
        """When config is not a salon, enabling both resets pos_is_salon and warns."""
        self.pos_config.is_salon = False
        settings = self.env['res.config.settings'].new({
            'pos_config_id': self.pos_config.id,
            'pos_is_salon': True,
            'pos_module_pos_restaurant': True,
        })
        res = settings._onchange_pos_salon_restaurant()
        self.assertFalse(settings.pos_is_salon)
        self.assertIn('warning', res)
        self.assertEqual(res['warning']['title'], 'Not allowed')
