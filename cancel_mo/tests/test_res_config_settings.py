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
    """Test cases for configuration settings in cancel_mo."""

    def setUp(self):
        super().setUp()
        self.config_parameter = self.env['ir.config_parameter'].sudo()
        self.config_parameter.search([
            ('key', 'in', [
                'cancel_mo.is_cancel_inventory_moves',
                'cancel_mo.is_cancel_workorder',
            ])
        ]).unlink()

    def test_default_values(self):
        """Test default values of configuration settings fields."""
        settings = self.env['res.config.settings'].create({})
        self.assertFalse(
            settings.is_cancel_inventory_moves,
            "is_cancel_inventory_moves should default to False when parameter is absent",
        )
        self.assertFalse(
            settings.is_cancel_workorder,
            "is_cancel_workorder should default to False when parameter is absent",
        )

    def test_set_and_get_values(self):
        """Test setting and getting configuration values via res.config.settings."""
        settings = self.env['res.config.settings'].create({
            'is_cancel_inventory_moves': True,
            'is_cancel_workorder': True,
        })
        settings.execute()

        self.assertEqual(
            self.config_parameter.get_str('cancel_mo.is_cancel_inventory_moves'),
            'True',
            "is_cancel_inventory_moves should be stored as 'True'",
        )
        self.assertEqual(
            self.config_parameter.get_str('cancel_mo.is_cancel_workorder'),
            'True',
            "is_cancel_workorder should be stored as 'True'",
        )

        new_settings = self.env['res.config.settings'].create({})
        self.assertTrue(
            new_settings.is_cancel_inventory_moves,
            "New settings should read True for is_cancel_inventory_moves from parameters",
        )
        self.assertTrue(
            new_settings.is_cancel_workorder,
            "New settings should read True for is_cancel_workorder from parameters",
        )

    def test_disable_settings(self):
        """Test disabling settings persists False in ir.config_parameter."""
        self.config_parameter.set_str('cancel_mo.is_cancel_inventory_moves', 'True')
        self.config_parameter.set_str('cancel_mo.is_cancel_workorder', 'True')

        settings = self.env['res.config.settings'].create({
            'is_cancel_inventory_moves': False,
            'is_cancel_workorder': False,
        })
        settings.execute()

        self.assertEqual(
            self.config_parameter.get_str('cancel_mo.is_cancel_inventory_moves'),
            'False',
            "is_cancel_inventory_moves should be updated to 'False'",
        )
        self.assertEqual(
            self.config_parameter.get_str('cancel_mo.is_cancel_workorder'),
            'False',
            "is_cancel_workorder should be updated to 'False'",
        )
