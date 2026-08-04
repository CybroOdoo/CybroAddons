# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase


class TestInterCompanyConfigSettings(TransactionCase):
    """Test the configuration settings for inter-company synchronization."""

    def test_sale_purchase_sync_setting(self):
        """Test enabling and disabling the inter-company synchronization parameter."""
        ResConfigSettings = self.env['res.config.settings']
        
        # Test enabling
        settings_on = ResConfigSettings.create({
            'sale_purchase_sync': True
        })
        settings_on.execute()
        
        param = self.env['ir.config_parameter'].sudo().get_param('inter_company_synchronization.sale_purchase_sync')
        self.assertTrue(param, "Config parameter should be set to True")
        
        # Test disabling
        settings_off = ResConfigSettings.create({
            'sale_purchase_sync': False
        })
        settings_off.execute()
        
        param_off = self.env['ir.config_parameter'].sudo().get_param('inter_company_synchronization.sale_purchase_sync')
        self.assertFalse(param_off, "Config parameter should be False/empty")
