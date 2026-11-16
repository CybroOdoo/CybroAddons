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
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for custom tip percentage in res.config.settings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Shop Settings Custom Tip',
            'custom_tip_percentage': 10.0,
        })

    def test_settings_read_custom_tip_percentage(self):
        """Test reading pos_custom_tip_percentage from res.config.settings."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
        })
        self.assertEqual(
            settings.pos_custom_tip_percentage,
            10.0,
            "Settings should reflect custom tip percentage from pos.config",
        )

    def test_settings_write_custom_tip_percentage(self):
        """Test updating pos_custom_tip_percentage via res.config.settings."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_custom_tip_percentage': 18.5,
        })
        settings.execute()
        self.assertEqual(
            self.pos_config.custom_tip_percentage,
            18.5,
            "pos.config custom_tip_percentage should be updated via settings",
        )

    def test_settings_update_custom_tip_percentage(self):
        """Test changing custom tip percentage back to zero or another value via settings."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_custom_tip_percentage': 25.0,
        })
        settings.execute()
        self.assertEqual(
            self.pos_config.custom_tip_percentage,
            25.0,
            "pos.config custom_tip_percentage should be updated to 25.0",
        )
