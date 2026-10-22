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

from twilio.base.exceptions import TwilioRestException

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import TwilioCommon

CLIENT = 'odoo.addons.odoo_twilio_sms.models.twilio_account.Client'
LOGGER = 'odoo.addons.odoo_twilio_sms.models.twilio_account'


@tagged('post_install', '-at_install')
class TestTwilioAccount(TwilioCommon):
    """Tests for testing the Twilio account connection."""

    def test_default_values(self):
        """A new account is in 'new' state with a default test message."""
        self.assertEqual(self.account.state, 'new')
        self.assertTrue(self.account.body)

    def test_credentials_hidden_from_users(self):
        """Internal users can use an account but not read its credentials."""
        user = self.env['res.users'].create({
            'name': 'Sales User',
            'login': 'twilio_sales_user',
            'group_ids': [(6, 0, self.env.ref('base.group_user').ids)],
        })
        account = self.account.with_user(user)
        self.assertEqual(account.name, 'Test Account')
        with self.assertRaises(AccessError):
            account.read(['auth_token'])
        with self.assertRaises(AccessError):
            account.write({'name': 'Changed'})

    def test_connection_success(self):
        """A sent test message confirms the account."""
        with patch(CLIENT) as client:
            client.return_value.messages.create.return_value.sid = 'SM123'
            action = self.account.action_test_connection()
        client.assert_called_once_with('AC123', 'TOKEN')
        client.return_value.messages.create.assert_called_once_with(
            body=self.account.body, from_='+15550000000', to='+15551111111')
        self.assertEqual(self.account.state, 'confirm')
        self.assertEqual(action['params']['type'], 'success')

    def test_connection_strips_credentials(self):
        """Spaces around the SID and token are removed."""
        self.account.write({'account_sid': ' AC123 ', 'auth_token': ' TOKEN '})
        with patch(CLIENT) as client:
            self.account.action_test_connection()
        client.assert_called_once_with('AC123', 'TOKEN')

    def test_connection_trial_account(self):
        """A trial account restriction still confirms the account."""
        error = TwilioRestException(400, 'uri', msg='Trial accounts cannot send', code=572006)
        with patch(CLIENT) as client:
            client.return_value.messages.create.side_effect = error
            action = self.account.action_test_connection()
        self.assertEqual(self.account.state, 'confirm')
        self.assertEqual(action['params']['type'], 'warning')

    @mute_logger(LOGGER)
    def test_connection_send_error(self):
        """Any other Twilio error while sending fails the connection."""
        error = TwilioRestException(400, 'uri', msg='Invalid To number', code=21211)
        with patch(CLIENT) as client:
            client.return_value.messages.create.side_effect = error
            action = self.account.action_test_connection()
        self.assertEqual(self.account.state, 'new')
        self.assertEqual(action['params']['type'], 'danger')
        self.assertIn('Invalid To number', action['params']['message'])

    @mute_logger(LOGGER)
    def test_connection_invalid_credentials(self):
        """Wrong credentials fail the connection without sending."""
        with patch(CLIENT) as client:
            client.return_value.api.v2010.accounts.return_value.fetch.side_effect = (
                Exception('Authenticate'))
            action = self.account.action_test_connection()
        client.return_value.messages.create.assert_not_called()
        self.assertEqual(self.account.state, 'new')
        self.assertEqual(action['params']['type'], 'danger')
        self.assertIn('Authenticate', action['params']['message'])
