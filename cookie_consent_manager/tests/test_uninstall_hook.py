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
from odoo.addons.cookie_consent_manager import uninstall_hook


@tagged('post_install', '-at_install')
class TestUninstallHook(TransactionCase):
    """Unit tests for the uninstall hook."""

    def test_uninstall_hook(self):
        """Test uninstall_hook removes cookie_consent_manager config parameters."""
        self.env['ir.config_parameter'].sudo().set_str(
            'cookie_consent_manager.cookie_template_id', '123'
        )
        self.assertTrue(
            self.env['ir.config_parameter'].search([
                ('key', '=', 'cookie_consent_manager.cookie_template_id')
            ])
        )

        uninstall_hook(self.env)

        self.assertFalse(
            self.env['ir.config_parameter'].search([
                ('key', '=', 'cookie_consent_manager.cookie_template_id')
            ])
        )
