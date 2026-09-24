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
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestAccountMoveTelegram(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bot = cls.env["telegram.bot"].create({
            "name": "Invoice Test Bot",
            "token": "invoice-token"
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Invoice Partner",
            "telegram_chat_id": "667788",
            "telegram_username": "invoice_partner_username",
            "telegram_opt_in": True,
            "telegram_bot_id": cls.bot.id,
        })
        # Create standard invoice (account.move)
        cls.invoice = cls.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": cls.partner.id,
        })

    def test_send_telegram_message_validations(self):
        """Test validation exceptions for Telegram options."""
        self.partner.telegram_opt_in = False
        with self.assertRaises(ValidationError):
            self.invoice.send_telegram_message("Test message", False, bot=self.bot)

    def test_send_telegram_message_success(self):
        """Test successful execution of send_telegram_message which creates a telegram.message and logs to chatter."""
        with patch.object(type(self.env["telegram.message"]), "send_via_bot", return_value=True) as mock_send:
            res = self.invoice.send_telegram_message("Valid Invoice Message", False, bot=self.bot)
            
        self.assertTrue(res)
        mock_send.assert_called_once()
        
        # Verify chatter log
        messages = self.invoice.message_ids
        chatter_bodies = [m.body for m in messages]
        self.assertTrue(any("Valid Invoice Message" in body for body in chatter_bodies))

    def test_action_send_telegram_wizard_returns(self):
        """Test action method returns valid action and context dictionary."""
        action = self.invoice.action_send_telegram()
        self.assertEqual(action["res_model"], "telegram.test")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["context"]["default_partner_id"], self.partner.id)
        self.assertEqual(action["context"]["default_invoice_id"], self.invoice.id)
