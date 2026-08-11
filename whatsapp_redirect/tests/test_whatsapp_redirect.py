# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from urllib.parse import quote
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

@tagged('post_install', '-at_install')
class TestWhatsappRedirect(TransactionCase):
    """Test cases for whatsapp redirect."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'phone': '+1234567890',
        })

    def test_res_partner_action_send_msg(self):
        """Test opening WhatsApp wizard."""
        action = self.partner.action_send_msg()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['name'], 'Whatsapp Message')
        self.assertEqual(
            action['res_model'],
            'whatsapp.send.message'
        )
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['target'], 'new')

        self.assertEqual(
            action['context']['default_user_id'],
            self.partner.id
        )

    def test_whatsapp_send_message_wizard_creation(self):
        """Test wizard creation."""
        wizard = self.env['whatsapp.send.message'].create({
            'user_id': self.partner.id,
            'message': 'Test message for WhatsApp',
        })

        self.assertEqual(wizard.user_id, self.partner)
        self.assertEqual(wizard.mobile, self.partner.phone)

        self.assertEqual(
            wizard.message,
            'Test message for WhatsApp'
        )

    def test_whatsapp_send_message_action_send_message(self):
        """Test WhatsApp URL generation."""
        message = 'Hello World'

        wizard = self.env['whatsapp.send.message'].create({
            'user_id': self.partner.id,
            'message': message,
        })

        action = wizard.action_send_message()

        expected_url = (
            "https://api.whatsapp.com/send?"
            f"phone=+1234567890&text={quote(message)}"
        )

        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['url'], expected_url)
        self.assertEqual(action['target'], 'new')

    def test_whatsapp_send_message_with_spaces(self):
        """Test message with spaces."""
        message = 'Hello World from Odoo'

        wizard = self.env['whatsapp.send.message'].create({
            'user_id': self.partner.id,
            'message': message,
        })

        action = wizard.action_send_message()

        expected_url = (
            "https://api.whatsapp.com/send?"
            f"phone=+1234567890&text={quote(message)}"
        )

        self.assertEqual(action['url'], expected_url)