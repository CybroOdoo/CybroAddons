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

class TestTelegramTestWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bot = cls.env["telegram.bot"].create({
            "name": "Wizard Bot",
            "token": "wizard-token"
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Wizard Partner",
            "telegram_chat_id": "999888",
            "telegram_username": "wizard_recipient",
            "telegram_opt_in": True,
            "telegram_bot_id": cls.bot.id,
        })
        cls.sale_order = cls.env["sale.order"].create({
            "partner_id": cls.partner.id,
        })
        
        cls.sale_model_id = cls.env["ir.model"].search([("model", "=", "sale.order")], limit=1)
        cls.template = cls.env["telegram.template"].create({
            "name": "SO Confirmation",
            "model_id": cls.sale_model_id.id,
            "message": "Hi, order is ready."
        })

    def test_default_get_populates_values(self):
        """Test wizard gets correct defaults from context details."""
        context = {
            "default_partner_id": self.partner.id,
            "default_sale_order_id": self.sale_order.id,
        }
        wizard = self.env["telegram.test"].with_context(context).create({
            "partner_id": self.partner.id,
            "message_text": "Direct message",
        })
        self.assertEqual(wizard.partner_id.id, self.partner.id)
        self.assertEqual(wizard.sale_order_id.id, self.sale_order.id)
        
        # Test current model compute
        wizard._compute_current_model()
        self.assertEqual(wizard.current_model_id.model, "sale.order")

    def test_onchange_telegram_template(self):
        """Test template changes update the wizard's dynamic message preview."""
        wizard = self.env["telegram.test"].create({
            "partner_id": self.partner.id,
            "sale_order_id": self.sale_order.id,
            "telegram_template_id": self.template.id,
        })
        
        wizard._onchange_telegram_template_id()
        self.assertTrue(wizard.message_text)
        self.assertIn("Hi, order is ready.", wizard.message_text)

    def test_action_send_invokes_document_sending(self):
        """Test clicking send in the wizard triggers document's send_telegram_message."""
        wizard = self.env["telegram.test"].create({
            "partner_id": self.partner.id,
            "sale_order_id": self.sale_order.id,
            "message_text": "Send from wizard!",
        })
        
        with patch.object(type(self.env["sale.order"]), "send_telegram_message", return_value=True) as mock_send_message:
            action = wizard.action_send()
            
        self.assertTrue(action)
        mock_send_message.assert_called_once_with(
            "Send from wizard!",
            wizard.telegram_template_id,
            attachment_ids=wizard.attachment_ids.ids
        )
