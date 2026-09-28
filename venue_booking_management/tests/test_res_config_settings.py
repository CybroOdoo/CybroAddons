# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase

class TestResConfigSettings(TransactionCase):

    def test_res_config_settings(self):
        """Test settings configuration."""
        Settings = self.env['res.config.settings']
        
        # Write config
        settings = Settings.create({
            'is_extra': True,
            'extra_amount': 50.0,
        })
        settings.execute()
        
        # Read back config
        is_extra = self.env['ir.config_parameter'].sudo().get_param('venue_booking_management.is_extra')
        extra_amount = self.env['ir.config_parameter'].sudo().get_param('venue_booking_management.extra_amount')
        
        self.assertTrue(is_extra)
        self.assertEqual(float(extra_amount), 50.0)
