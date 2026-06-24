# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

class TestResConfigSettings(TransactionCase):

    def test_res_config_settings(self):
        """ Test default value of fleet_service_product_id """
        ResConfig = self.env['res.config.settings']
        config = ResConfig.new()
        
        # It should fall back to False if no fleet_service_product is found or return its ID
        try:
            expected_id = self.env.ref('fleet_rental.fleet_service_product').id
            param_id = self.env['ir.config_parameter'].sudo().get_param('fleet_rental.fleet_service_product_id')
            if param_id:
                self.assertEqual(config.fleet_service_product_id.id, int(param_id))
            else:
                self.assertFalse(config.fleet_service_product_id)
        except ValueError:
            self.assertFalse(config.fleet_service_product_id)
