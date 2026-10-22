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
#############################################################################
from unittest.mock import patch

from twilio.base.exceptions import TwilioException

from odoo.tests import tagged

from .common import TwilioCommon

CLIENT = 'odoo.addons.odoo_twilio_sms.models.twilio_account.Client'


@tagged('post_install', '-at_install')
class TestSmsBuilder(TwilioCommon):
    """Tests for the send SMS wizard."""

    def _create_wizard(self, **vals):
        """Create the wizard for the first partner."""
        return self.env['sms.builder'].with_context(
            default_partner_id=self.partner_1.id,
        ).create({
            'account_id': self.account.id,
            **({} if 'template_id' in vals else {'text_message': 'Your order is ready'}),
            **vals,
        })

    def test_partner_number(self):
        """The recipient number comes from the partner."""
        wizard = self._create_wizard()
        self.assertEqual(wizard.receiving_number, '+15552222222')

    def test_template_fills_message(self):
        """Choosing a template copies its content."""
        wizard = self._create_wizard(template_id=self.template.id)
        self.assertEqual(wizard.text_message, 'Hello from Odoo')

    def test_edit_number_keeps_partner_phone(self):
        """Changing the number in the wizard does not change the contact."""
        wizard = self._create_wizard()
        wizard.receiving_number = '+15559999999'
        self.assertEqual(self.partner_1.phone, '+15552222222')
        self.assertEqual(wizard.receiving_number, '+15559999999')

    def test_edit_message_keeps_template(self):
        """Changing the message does not change the template."""
        wizard = self._create_wizard(template_id=self.template.id)
        wizard.text_message = 'Changed text'
        self.assertEqual(self.template.content, 'Hello from Odoo')

    def test_custom_message_without_template(self):
        """A message typed without template is kept and sent."""
        wizard = self._create_wizard()
        self.assertEqual(wizard.text_message, 'Your order is ready')

    def test_send_sms(self):
        """The message is sent from the account number to the partner."""
        wizard = self._create_wizard()
        with patch(CLIENT) as client:
            client.return_value.messages.create.return_value.sid = 'SM123'
            action = wizard.action_confirm_sms()
        client.assert_called_once_with('AC123', 'TOKEN')
        client.return_value.messages.create.assert_called_once_with(
            body='Your order is ready', from_='+15550000000', to='+15552222222')
        self.assertEqual(action['params']['type'], 'success')

    def test_send_without_sid(self):
        """A message without SID is reported as not sent."""
        wizard = self._create_wizard()
        with patch(CLIENT) as client:
            client.return_value.messages.create.return_value.sid = None
            action = wizard.action_confirm_sms()
        self.assertEqual(action['params']['type'], 'warning')

    def test_send_error(self):
        """A Twilio error is reported as not sent."""
        wizard = self._create_wizard()
        with patch(CLIENT) as client:
            client.return_value.messages.create.side_effect = TwilioException('error')
            action = wizard.action_confirm_sms()
        self.assertEqual(action['params']['type'], 'warning')
