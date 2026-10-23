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
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for 'res.config.settings' model in hr_linkedin_recruitment."""

    def test_set_values(self):
        """Test set_values saves li_username and li_password to ir.config_parameter."""
        settings = self.env['res.config.settings'].create({
            'li_username': 'test_li_user@example.com',
            'li_password': 'test_secret_password_123',
        })
        settings.set_values()
        get_param = self.env['ir.config_parameter'].sudo().get_str
        self.assertEqual(get_param('recruitment.li_username'), 'test_li_user@example.com')
        self.assertEqual(get_param('recruitment.li_password'), 'test_secret_password_123')

    def test_get_values(self):
        """Test get_values loads li_username and li_password from ir.config_parameter."""
        set_param = self.env['ir.config_parameter'].sudo().set_str
        set_param('recruitment.li_username', 'loaded_user@example.com')
        set_param('recruitment.li_password', 'loaded_pass_456')
        settings = self.env['res.config.settings'].create({})
        values = settings.get_values()
        self.assertEqual(values.get('li_username'), 'loaded_user@example.com')
        self.assertEqual(values.get('li_password'), 'loaded_pass_456')
