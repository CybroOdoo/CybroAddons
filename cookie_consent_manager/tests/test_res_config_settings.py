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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Unit tests for cookie template settings in res.config.settings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cookie_info = cls.env['cookie.information'].create({
            'template_title': 'Config Test Template',
            'pop_up_text': 'Testing cookie settings',
        })

    def test_res_config_settings(self):
        """Test setting and getting cookie_template_id in res.config.settings."""
        settings = self.env['res.config.settings'].create({
            'cookie_template_id': self.cookie_info.id,
        })
        settings.execute()

        param_val = self.env['ir.config_parameter'].sudo().get_str(
            'cookie_consent_manager.cookie_template_id'
        )
        self.assertEqual(param_val, str(self.cookie_info.id))

        new_settings = self.env['res.config.settings'].new({})
        self.assertEqual(new_settings.cookie_template_id.id, self.cookie_info.id)
