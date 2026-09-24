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
import base64
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from ..models import telegram_message as telegram_message_model

class FakeResponse:
    def __init__(self, json_data=None, text="", content=b"", raise_error=None):
        self._json_data = json_data or {}
        self.text = text
        self.content = content
        self._raise_error = raise_error

    def raise_for_status(self):
        if self._raise_error:
            raise self._raise_error

    def json(self):
        return self._json_data

class TestTelegramMessage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bot = cls.env["telegram.bot"].create({
            "name": "Test Bot",
            "token": "bot-test-token",
            "webhook_url": "https://example.com/webhook",
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Alex",
            "telegram_chat_id": "777888",
            "telegram_username": "alex_username",
            "telegram_opt_in": True,
            "telegram_bot_id": cls.bot.id,
        })

    def test_create_incoming_existing_username(self):
        """Test incoming message with username matching existing partner."""
        payload = {
            "message": {
                "message_id": 100,
                "chat": {
                    "id": 777888,
                    "username": "alex_username",
                    "first_name": "Alex",
                },
                "text": "Hello, world",
            }
        }
        with patch.object(type(self.env["telegram.message"]), "_handle_telegram_attachments", return_value=False):
            message = self.env["telegram.message"].create_incoming(self.bot, payload)

        self.assertEqual(message.partner_id.id, self.partner.id)
        self.assertEqual(message.message_text, "Hello, world")
        self.assertEqual(message.state, "received")

    def test_create_incoming_new_partner(self):
        """Test incoming message creates a new partner if none matches."""
        payload = {
            "message": {
                "message_id": 101,
                "chat": {
                    "id": 999111,
                    "username": "unknown_user",
                    "first_name": "Bob",
                    "last_name": "Builder",
                },
                "text": "Help please",
            }
        }
        with patch.object(type(self.env["telegram.message"]), "_handle_telegram_attachments", return_value=False):
            message = self.env["telegram.message"].create_incoming(self.bot, payload)

        self.assertEqual(message.partner_id.name, "Bob Builder")
        self.assertEqual(message.partner_id.telegram_chat_id, "999111")
        self.assertEqual(message.partner_id.telegram_username, "unknown_user")

    def test_send_via_bot_success(self):
        """Test successful send of message and attachment."""
        attachment = self.env["ir.attachment"].create({
            "name": "invoice_doc.pdf",
            "type": "binary",
            "datas": base64.b64encode(b"pdf-content"),
            "mimetype": "application/pdf",
        })
        message = self.env["telegram.message"].create({
            "direction": "outgoing",
            "chat_id": "777888",
            "partner_id": self.partner.id,
            "bot_id": self.bot.id,
            "message_text": "Here is invoice",
            "attachment_ids": [(6, 0, attachment.ids)],
            "state": "new",
        })
        with patch.object(telegram_message_model.requests, "post", return_value=FakeResponse()) as mock_post:
            message.send_via_bot("Here is invoice", bot=self.bot)

        self.assertEqual(message.state, "sent")
        self.assertEqual(mock_post.call_count, 2)
        # Check text send payload
        text_api_call = mock_post.call_args_list[0]
        self.assertEqual(text_api_call.args[0], "https://api.telegram.org/botbot-test-token/sendMessage")
        self.assertEqual(text_api_call.kwargs["json"]["text"], "Here is invoice")
        # Check doc send payload
        doc_api_call = mock_post.call_args_list[1]
        self.assertEqual(doc_api_call.args[0], "https://api.telegram.org/botbot-test-token/sendDocument")
        self.assertEqual(doc_api_call.kwargs["data"]["chat_id"], "777888")

    def test_handle_telegram_attachments_photo(self):
        """Test downloading photo file and creating PDF attachment in Odoo."""
        message = self.env["telegram.message"].create({
            "chat_id": "777888",
            "partner_id": self.partner.id,
            "bot_id": self.bot.id,
            "message_text": "Sent a photo",
            "state": "received",
        })
        payload = {
            "photo": [
                {"file_id": "low-res-id", "file_unique_id": "un-low"},
                {"file_id": "photo-file-id", "file_unique_id": "photo-un-high"}
            ]
        }
        res_info = FakeResponse(json_data={"ok": True, "result": {"file_path": "photos/high.jpg"}})
        res_download = FakeResponse(content=b"pure-binary-img-bytes")
        
        with patch.object(telegram_message_model.requests, "get", side_effect=[res_info, res_download]):
            attachment = message._handle_telegram_attachments(self.bot, message, payload)

        self.assertTrue(attachment)
        self.assertEqual(attachment.name, "photo_photo-un-high.jpg")
        self.assertEqual(attachment.mimetype, "image/jpeg")
        self.assertEqual(message.attachment_ids.ids, attachment.ids)
