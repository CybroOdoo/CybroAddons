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

class TestSaleOrderTelegram(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bot = cls.env["telegram.bot"].create({
            "name": "Sale Test Bot",
            "token": "sale-token"
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Sale Partner",
            "telegram_chat_id": "445566",
            "telegram_username": "sale_partner_username",
            "telegram_opt_in": True,
            "telegram_bot_id": cls.bot.id,
        })
        cls.sale_order = cls.env["sale.order"].create({
            "partner_id": cls.partner.id,
        })

    def test_send_telegram_message_validations(self):
        """Test validation exceptions for Telegram options."""
        # Case 1: Opt-in disabled
        self.partner.telegram_opt_in = False
        with self.assertRaises(ValidationError):
            self.sale_order.send_telegram_message("Test message", False, bot=self.bot)
            
        # Case 2: Missing Chat ID
        self.partner.telegram_opt_in = True
        self.partner.telegram_chat_id = False
        with self.assertRaises(ValidationError):
            self.sale_order.send_telegram_message("Test message", False, bot=self.bot)
            
        # Case 3: Missing Bot
        self.partner.telegram_chat_id = "445566"
        self.partner.telegram_bot_id = False
        with self.assertRaises(ValidationError):
            self.sale_order.send_telegram_message("Test message", False, bot=False)

    def test_send_telegram_message_success(self):
        """Test successful execution of send_telegram_message which creates a telegram.message and logs to chatter."""
        with patch.object(type(self.env["telegram.message"]), "send_via_bot", return_value=True) as mock_send:
            res = self.sale_order.send_telegram_message("Valid SO Message", False, bot=self.bot)
            
        self.assertTrue(res)
        mock_send.assert_called_once()
        
        # Verify chatter log
        messages = self.sale_order.message_ids
        chatter_bodies = [m.body for m in messages]
        self.assertTrue(any("Valid SO Message" in body for body in chatter_bodies))

    def test_action_send_telegram_wizard_returns(self):
        """Test action method returns valid action and context dictionary."""
        action = self.sale_order.action_send_telegram()
        self.assertEqual(action["res_model"], "telegram.test")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["context"]["default_partner_id"], self.partner.id)
        self.assertEqual(action["context"]["default_sale_order_id"], self.sale_order.id)
