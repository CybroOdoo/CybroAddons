# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    """Test cases for res.config.settings multi_pricelist extension"""

    def test_set_values_stores_param(self):
        """set_values should persist multi_pricelist as an ir.config_parameter"""

        settings = self.env['res.config.settings'].create({
            'multi_pricelist': True,
        })
        settings.set_values()

        param = self.env['ir.config_parameter'].sudo().get_str(
            'multi_pricelist.multi_pricelist'
        )

        self.assertTrue(
            param,
            "Parameter should be truthy after set_values(True)"
        )

    def test_set_values_false(self):
        """Switching the setting off must really turn it off"""
        self.env['res.config.settings'].create(
            {'multi_pricelist': True}).set_values()
        self.env['res.config.settings'].create(
            {'multi_pricelist': False}).set_values()

        param = self.env['ir.config_parameter'].sudo().get_str(
            'multi_pricelist.multi_pricelist'
        )

        self.assertNotIn(param, ('True', 'true', '1'))
        self.assertFalse(
            self.env['res.config.settings'].create({}).multi_pricelist)

    def test_get_values_returns_key(self):
        """get_values should include the multi_pricelist key"""

        settings = self.env['res.config.settings'].create({
            'multi_pricelist': True,
        })
        settings.set_values()

        values = settings.get_values()

        self.assertIn(
            'multi_pricelist',
            values,
            "get_values() result must contain 'multi_pricelist' key",
        )

    def test_get_set_roundtrip(self):
        """Value written by set_values should be readable by get_values"""

        settings = self.env['res.config.settings'].create({
            'multi_pricelist': True,
        })
        settings.set_values()

        values = settings.get_values()

        # The stored param is a string 'True'; the field coerces it to bool
        self.assertTrue(
            values.get('multi_pricelist'),
            "get_values() should reflect the value written by set_values()",
        )
