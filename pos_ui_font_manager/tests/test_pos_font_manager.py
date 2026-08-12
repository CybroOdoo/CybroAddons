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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase

class TestPosFontManager(TransactionCase):

    def setUp(self):
        super(TestPosFontManager, self).setUp()
        self.PosConfig = self.env['pos.config']
        self.ResConfigSettings = self.env['res.config.settings']
        
        self.pos_config = self.PosConfig.create({
            'name': 'Test POS Config for Font Manager',
        })

    def test_01_default_font_settings(self):
        """Test the default values when a new POS config is created."""
        self.assertEqual(self.pos_config.pos_font_preset, 'medium', "Default font preset should be 'medium'")
        self.assertEqual(self.pos_config.pos_global_scale, 100, "Default global scale should be 100")
        self.assertEqual(self.pos_config.pos_product_card_font_size, 0, "Default custom font size should be 0")

    def test_02_res_config_settings_propagation(self):
        """Test if changes in res.config.settings correctly propagate to pos.config."""
        settings = self.ResConfigSettings.create({
            'pos_config_id': self.pos_config.id,
            'pos_font_preset': 'large',
            'pos_global_scale': 120,
            'pos_product_price_font_size': 18,
            'pos_ticket_screen_font_size': 14,
        })
        
        settings.execute()
        
        self.assertEqual(self.pos_config.pos_font_preset, 'large', "Font preset should have been updated to 'large'")
        self.assertEqual(self.pos_config.pos_global_scale, 120, "Global scale should have been updated to 120")
        self.assertEqual(self.pos_config.pos_product_price_font_size, 18, "Product price font size should update to 18")
        self.assertEqual(self.pos_config.pos_ticket_screen_font_size, 14, "Ticket screen font size should update to 14")
