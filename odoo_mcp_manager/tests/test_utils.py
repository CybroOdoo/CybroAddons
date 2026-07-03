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
from ..utils import bot_auth

class TestUtils(TransactionCase):

    def test_01_validate_bot_api_key(self):
        """Test bot API key validation."""
        self.env['ir.config_parameter'].sudo().set_param('bot_gateway.webhook_secret', 'valid-key')
        
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
