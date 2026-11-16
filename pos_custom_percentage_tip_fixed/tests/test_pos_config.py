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
class TestPosConfig(TransactionCase):
    """Test cases for custom tip percentage in pos.config."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Shop Custom Tip',
        })

    def test_default_custom_tip_percentage(self):
        """Test default value of custom_tip_percentage."""
        self.assertEqual(
            self.pos_config.custom_tip_percentage,
            0.0,
            "Default custom tip percentage should be 0.0",
        )

    def test_set_custom_tip_percentage(self):
        """Test assigning a custom tip percentage on pos.config."""
        self.pos_config.write({'custom_tip_percentage': 15.0})
        self.assertEqual(
            self.pos_config.custom_tip_percentage,
            15.0,
            "Custom tip percentage should be updated to 15.0",
        )

    def test_update_custom_tip_percentage(self):
        """Test updating custom tip percentage value."""
        self.pos_config.write({'custom_tip_percentage': 20.5})
        self.assertEqual(
            self.pos_config.custom_tip_percentage,
            20.5,
            "Custom tip percentage should be updated to 20.5",
        )
