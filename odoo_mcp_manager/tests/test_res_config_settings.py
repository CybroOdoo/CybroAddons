# -*- coding: utf-8 -*-
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
