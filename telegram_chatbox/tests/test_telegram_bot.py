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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch
from requests.exceptions import ConnectionError, Timeout
from odoo.tests.common import TransactionCase
from ..models import telegram_bot as telegram_bot_model

class FakeResponse:
    def __init__(self, json_data=None, text="", raise_error=None):
        self._json_data = json_data or {}
        self.text = text
        self._raise_error = raise_error

    def raise_for_status(self):
        if self._raise_error:
            raise self._raise_error

    def json(self):
        return self._json_data

class TestTelegramBot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bot = cls.env["telegram.bot"].create({
            "name": "Test Bot",
            "token": "bot-test-token",
            "webhook_url": "https://example.com/webhook",
            "timeout": 10,
        })

    def test_crud_overrides(self):
        """Test standard custom create and write methods run without exceptions."""
        bot = self.env["telegram.bot"].create({
            "name": "Another Bot",
            "token": "other-token",
        })
        self.assertTrue(bot)
        bot.write({"name": "Updated Bot"})
        self.assertEqual(bot.name, "Updated Bot")

    def test_get_by_token(self):
        """Test retrieving bot record using its token."""
        found_bot = self.env["telegram.bot"].get_by_token("bot-test-token")
        self.assertEqual(found_bot.id, self.bot.id)
        
        non_existent = self.env["telegram.bot"].get_by_token("fake-token")
        self.assertFalse(non_existent)

    def test_action_set_webhook_success(self):
        """Test successful registration of setWebhook."""
        response = FakeResponse(
            json_data={"ok": True, "description": "Webhook set successfully"},
            text="ok",
        )
        with patch.object(telegram_bot_model.requests, "post", return_value=response) as mock_post:
            action = self.bot.action_set_webhook()

        self.assertEqual(self.bot.status, "active")
        self.assertTrue(self.bot.last_sync)
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "success")
        mock_post.assert_called_once_with(
            "https://api.telegram.org/botbot-test-token/setWebhook",
            json={"url": self.bot.webhook_url},
            timeout=self.bot.timeout,
        )

    def test_action_set_webhook_connection_error(self):
        """Test setWebhook failure via connection exception."""
        with patch.object(
            telegram_bot_model.requests,
            "post",
            side_effect=ConnectionError("Host unreachable"),
        ):
            with patch.object(telegram_bot_model._logger, "warning") as mock_log:
                action = self.bot.action_set_webhook()

        self.assertEqual(self.bot.status, "error")
        self.assertEqual(action["params"]["title"], "Connection Failed")
        self.assertEqual(action["params"]["type"], "danger")

    def test_action_set_webhook_generic_error(self):
        """Test setWebhook failure via general exception."""
        with patch.object(
            telegram_bot_model.requests,
            "post",
            side_effect=Exception("Unexpected API error"),
        ):
            with patch.object(telegram_bot_model._logger, "error") as mock_log:
                action = self.bot.action_set_webhook()

        self.assertEqual(self.bot.status, "error")
        self.assertEqual(action["params"]["title"], "Error")
        self.assertEqual(action["params"]["type"], "danger")
