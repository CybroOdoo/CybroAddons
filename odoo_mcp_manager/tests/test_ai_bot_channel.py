# -*- coding: utf-8 -*-
import requests
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestAiBotChannel(TransactionCase):

    def setUp(self):
        super(TestAiBotChannel, self).setUp()
        self.channel = self.env['ai.bot.channel'].create({
            'name': 'Test Telegram Bot',
            'platform': 'telegram',
            'api_token': '123456789:ABCDEF',
        })
        self.env['ir.config_parameter'].sudo().set_param('web.base.url', 'https://odoo.example.com')
        self.env['ir.config_parameter'].sudo().set_param('bot_gateway.webhook_secret', 'secret-key')

    def test_01_compute_urls(self):
        """Test webhook URL computation."""
        self.channel._compute_urls()
        self.assertIn('https://odoo.example.com/bot/telegram?secret=secret-key', self.channel.webhook_url)

    @patch('requests.get')
    @patch('requests.post')
    def test_02_connect_telegram_success(self, mock_post, mock_get):
        """Test successful telegram connection."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'ok': True, 'result': {'username': 'test_bot'}}
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'ok': True}

        self.channel.action_connect()
        self.assertEqual(self.channel.status, 'active')
        self.assertEqual(self.channel.bot_username, 'test_bot')

    def test_03_disconnect(self):
        """Test disconnecting the channel."""
        self.channel.status = 'active'
        self.channel.bot_username = 'test_bot'
        self.channel.action_disconnect()
        self.assertEqual(self.channel.status, 'draft')
        self.assertFalse(self.channel.bot_username)
