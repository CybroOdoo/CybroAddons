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
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResConfigSettings(TransactionCase):

    def test_res_config_settings(self):
        """ Test default value of fleet_service_product_id """
        ResConfig = self.env['res.config.settings']
        config = ResConfig.new()

        product = self.env.ref('fleet_rental.fleet_service_product', raise_if_not_found=False)
        param_id = self.env['ir.config_parameter'].sudo().get_str('fleet_rental.fleet_service_product_id')
        if param_id:
            self.assertEqual(config.fleet_service_product_id.id, int(param_id))
        elif product:
            self.assertEqual(config.fleet_service_product_id, product)
        else:
            self.assertFalse(config.fleet_service_product_id)

    def test_get_default_product_exception(self):
        """ Test _get_default_product when ref raises ValueError """
        ResConfig = self.env['res.config.settings']
        with patch.object(self.env, 'ref', side_effect=ValueError):
            res = ResConfig._get_default_product()
            self.assertFalse(res)

    def test_custom_fleet_service_product_setting(self):
        """ Test setting and retrieving a custom fleet_service_product_id """
        custom_product = self.env['product.template'].create({
            'name': 'Custom Rental Service',
            'type': 'service',
        })
        self.env['ir.config_parameter'].sudo().set_int('fleet_rental.fleet_service_product_id', custom_product.id)
        contract = self.env['car.rental.contract'].new()
        self.assertEqual(contract._get_fleet_service_product(), custom_product)
