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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for POS all orders configuration in res.config.settings."""

    def setUp(self):
        super().setUp()
        self.settings_model = self.env['res.config.settings']
        self.icp = self.env['ir.config_parameter'].sudo()

    def test_default_values(self):
        """Test retrieving default values when parameters are not set."""
        self.icp.set_str('pos_all_orders.pos_all_order', False)
        self.icp.set_int('pos_all_orders.n_days', 0)
        settings = self.settings_model.create({})
        values = settings.get_values()
        self.assertFalse(values.get('pos_all_order'))
        self.assertEqual(values.get('n_days'), 0)

    def test_set_and_get_current_session(self):
        """Test setting and getting current_session configuration."""
        settings = self.settings_model.create({
            'pos_all_order': 'current_session',
            'n_days': 0,
        })
        settings.set_values()
        values = settings.get_values()
        self.assertEqual(values.get('pos_all_order'), 'current_session')
        self.assertEqual(self.icp.get_str('pos_all_orders.pos_all_order'), 'current_session')

    def test_set_and_get_last_n_days(self):
        """Test setting and getting last_n days configuration."""
        settings = self.settings_model.create({
            'pos_all_order': 'last_n',
            'n_days': 15,
        })
        settings.set_values()
        values = settings.get_values()
        self.assertEqual(values.get('pos_all_order'), 'last_n')
        self.assertEqual(values.get('n_days'), 15)
        self.assertEqual(self.icp.get_str('pos_all_orders.pos_all_order'), 'last_n')
        self.assertEqual(self.icp.get_int('pos_all_orders.n_days'), 15)

    def test_reset_config_values(self):
        """Test clearing or resetting configuration values."""
        settings = self.settings_model.create({
            'pos_all_order': False,
            'n_days': 0,
        })
        settings.set_values()
        values = settings.get_values()
        self.assertFalse(values.get('pos_all_order'))
        self.assertEqual(values.get('n_days'), 0)
