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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Unit tests for res.config.settings restriction fields."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and pos.config record."""
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Config Settings Store',
            'pos_restaurant_restriction': False,
            'pos_orderline_quantity_update': False,
            'pos_orderline_delete': False,
            'pos_order_delete': False,
            'pos_session_close': False,
        })

    def test_settings_toggle_propagates_to_pos_config(self):
        """Verify modifying settings fields updates the related pos.config record."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_orderline_quantity_update': True,
            'pos_restaurant_restriction': True,
            'pos_session_close': True,
            'pos_order_delete': True,
            'pos_orderline_delete': True,
        })
        self.assertTrue(self.pos_config.pos_restaurant_restriction)
        self.assertTrue(self.pos_config.pos_orderline_quantity_update)
        self.assertTrue(self.pos_config.pos_orderline_delete)
        self.assertTrue(self.pos_config.pos_order_delete)
        self.assertTrue(self.pos_config.pos_session_close)

        settings.write({
            'pos_order_delete': False,
            'pos_session_close': False,
        })
        self.assertFalse(self.pos_config.pos_order_delete)
        self.assertFalse(self.pos_config.pos_session_close)

    def test_settings_reads_values_from_pos_config(self):
        """Verify that res.config.settings correctly reflects pos.config values."""
        self.pos_config.write({
            'pos_restaurant_restriction': True,
            'pos_orderline_delete': True,
        })
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
        })
        self.assertTrue(settings.pos_restaurant_restriction)
        self.assertTrue(settings.pos_orderline_delete)
        self.assertFalse(settings.pos_orderline_quantity_update)
