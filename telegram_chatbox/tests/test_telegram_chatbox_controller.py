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
import json
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from ..controllers import telegram_chatbox as controller_module

class FakeHttpRequest:
    def __init__(self, data):
        self.data = data

class FakeRequest:
    def __init__(self, env, payload):
        self.env = env
        self.httprequest = FakeHttpRequest(payload)

class TestTelegramChatboxController(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bot = cls.env["telegram.bot"].create({
            "name": "Controller Bot",
            "token": "controller-token-123",
            "webhook_url": "https://example.com/webhook",
        })

    def test_telegram_webhook_returns_404_for_invalid_token(self):
        """Test that invalid token returns HTTP 404 with error JSON."""
        controller = controller_module.TelegramWebhookController()
        fake_request = FakeRequest(self.env, b"{}")

        with patch.object(controller_module, "request", fake_request):
            response = controller.telegram_webhook("wrong-token-abc")

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data["error"], "Invalid bot token")

    def test_telegram_webhook_processes_valid_payload(self):
        """Test webhook executes correctly under valid token and webhook body."""
        controller = controller_module.TelegramWebhookController()
        payload = {"message": {"message_id": 999, "chat": {"id": 111}, "text": "Heey"}}
        fake_request = FakeRequest(self.env, json.dumps(payload).encode("utf-8"))

        with patch.object(controller_module, "request", fake_request):
            with patch.object(
                type(self.env["telegram.message"]),
                "create_incoming",
                autospec=True,
                return_value=self.env["telegram.message"],
            ) as mock_create:
                response = controller.telegram_webhook(self.bot.token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.get_data(as_text=True))["ok"], True)
        self.assertTrue(self.bot.last_sync)
        mock_create.assert_called_once()

    def test_telegram_webhook_returns_500_on_processing_error(self):
        """Test that unexpected pipeline exception returns HTTP 500 containing error trace/message."""
        controller = controller_module.TelegramWebhookController()
        payload = {"message": {"message_id": 888}}
        fake_request = FakeRequest(self.env, json.dumps(payload).encode("utf-8"))

        with patch.object(controller_module, "request", fake_request):
            with patch.object(
                type(self.env["telegram.message"]),
                "create_incoming",
                autospec=True,
                side_effect=Exception("Database lock error"),
            ):
                with patch.object(controller_module._logger, "exception") as mock_log:
                    response = controller.telegram_webhook(self.bot.token)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.get_data(as_text=True))["error"], "Database lock error")
        mock_log.assert_called_once()
