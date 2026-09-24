# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from ..utils import bot_auth

class TestUtils(TransactionCase):

    def test_01_validate_bot_api_key(self):
        """Test bot API key validation."""
        self.env['ir.config_parameter'].sudo().set_str('bot_gateway.webhook_secret', 'valid-key')
        
        self.assertTrue(bot_auth.validate_bot_api_key(self.env, 'valid-key'))
        self.assertFalse(bot_auth.validate_bot_api_key(self.env, 'invalid-key'))
        self.assertFalse(bot_auth.validate_bot_api_key(self.env, ''))

    def test_02_check_rate_limit(self):
        """Test rate limiting logic."""
        ip = '127.0.0.1'
        # Reset the store for testing (since it's a global variable)
        bot_auth._rate_store[ip] = []
        
        # Test under limit
        for i in range(bot_auth.RATE_LIMIT):
            self.assertTrue(bot_auth.check_rate_limit(ip))
            
        # Test over limit
        self.assertFalse(bot_auth.check_rate_limit(ip))
