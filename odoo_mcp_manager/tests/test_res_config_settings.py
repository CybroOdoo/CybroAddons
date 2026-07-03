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

    def test_01_generate_webhook_secret(self):
        """Test generating and saving the webhook secret."""
        config = self.env['res.config.settings'].create({})
        config.action_generate_webhook_secret()
        secret = self.env['ir.config_parameter'].sudo().get_param('bot_gateway.webhook_secret')
        self.assertTrue(secret)
        self.assertEqual(config.bot_webhook_secret, secret)

    def test_02_generate_mcp_api_key(self):
        """Test generating and saving the MCP API key."""
        config = self.env['res.config.settings'].create({})
        config.action_generate_mcp_api_key()
        key = self.env['ir.config_parameter'].sudo().get_param('bot_gateway.mcp_api_key')
        self.assertTrue(key)
        self.assertEqual(config.bot_mcp_api_key, key)
