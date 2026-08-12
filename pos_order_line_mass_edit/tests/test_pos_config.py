# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosConfig(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a new POS Config for testing
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Shop Config',
        })

    def test_pos_config_default_mass_edit_button(self):
        """Test that show_mass_edit_button is enabled by default on pos.config"""
        self.assertTrue(
            self.pos_config.show_mass_edit_button,
            "The default value of show_mass_edit_button should be True"
        )

    def test_pos_config_write_mass_edit_button(self):
        """Test changing show_mass_edit_button on pos.config"""
        self.pos_config.write({'show_mass_edit_button': False})
        self.assertFalse(
            self.pos_config.show_mass_edit_button,
            "The show_mass_edit_button should be set to False"
        )
