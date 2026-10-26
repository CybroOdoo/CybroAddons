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
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestOpenAIOdooBase(TransactionCase):
    """Test suite for OpenAI Base Configuration in Odoo."""

    def test_openai_api_key_setting(self):
        """Test setting and retrieving the OpenAI API key via res.config.settings."""
        test_key = "sk-test-openai-api-key-12345"
        settings = self.env['res.config.settings'].create({
            'openai_api_key': test_key,
        })
        settings.execute()

        # Check parameter was saved in ir.config_parameter
        saved_key = self.env['ir.config_parameter'].sudo().get_str('openai_api_key')
        self.assertEqual(saved_key, test_key)

        # Check loading settings retrieves the key
        new_settings = self.env['res.config.settings'].new({})
        self.assertEqual(new_settings.openai_api_key, test_key)

    def test_openai_api_key_security(self):
        """Test that regular non-admin users cannot access openai_api_key."""
        regular_user = new_test_user(
            self.env,
            login='openai_regular_user',
            password='TestPassword123!',
            name='OpenAI Regular User',
            groups='base.group_user',
        )
        settings = self.env['res.config.settings'].with_user(regular_user)
        with self.assertRaises(AccessError):
            settings.read(['openai_api_key'])
