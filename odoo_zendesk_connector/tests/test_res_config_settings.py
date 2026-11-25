# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.settings_model = cls.env['res.config.settings']
        cls.api = cls.env['zendesk.api']
        cls.api_cls = type(cls.api)

    def setUp(self):
        super().setUp()
        self.api._set_param('company_domain', 'testdomain')
        self.api._set_param('client_id', 'test_client_id')
        self.api._set_param('client_secret', 'test_client_secret')
        self.api._set_param('scope', 'read write')
        self.api._set_param('is_connect_zendesk', 'True')
        self.api._set_param('access_token', 'initial_token')

    def test_set_values_clears_token_when_credentials_change(self):
        settings = self.settings_model.create({
            'company_domain': 'changed_domain',
            'zendesk_client_id': 'test_client_id',
            'zendesk_client_secret': 'test_client_secret',
            'zendesk_scope': 'read write',
        })
        with patch.object(self.api_cls, '_clear_token') as mock_clear:
            settings.set_values()
            mock_clear.assert_called_once()

    def test_set_values_keeps_token_when_credentials_unchanged(self):
        settings = self.settings_model.create({
            'company_domain': 'testdomain',
            'zendesk_client_id': 'test_client_id',
            'zendesk_client_secret': 'test_client_secret',
            'zendesk_scope': 'read write',
        })
        with patch.object(self.api_cls, '_clear_token') as mock_clear:
            settings.set_values()
            mock_clear.assert_not_called()

    def test_action_test_connection_disabled(self):
        settings = self.settings_model.create({
            'is_connect_zendesk': False,
            'company_domain': 'testdomain',
            'zendesk_client_id': 'test_client_id',
            'zendesk_client_secret': 'test_client_secret',
        })
        res = settings.action_test_connection()
        self.assertEqual(res['params']['type'], 'danger')
        self.assertIn("Please enable 'Connect Zendesk' first", res['params']['message'])

    def test_action_test_connection_missing_credentials(self):
        settings = self.settings_model.create({
            'is_connect_zendesk': True,
            'company_domain': '',
            'zendesk_client_id': 'test_client_id',
            'zendesk_client_secret': '',
        })
        res = settings.action_test_connection()
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['params']['type'], 'danger')
        self.assertIn('Please fill in the Company Domain', res['params']['message'])

    def test_action_test_connection_failure_during_fetch_or_request(self):
        settings = self.settings_model.create({
            'is_connect_zendesk': True,
            'company_domain': 'testdomain',
            'zendesk_client_id': 'test_client_id',
            'zendesk_client_secret': 'test_client_secret',
            'zendesk_scope': 'read write',
        })
        with patch.object(self.api_cls, '_fetch_access_token', side_effect=UserError("Authentication failed")):
            res = settings.action_test_connection()
            self.assertEqual(res['params']['type'], 'danger')
            self.assertIn("Authentication failed", res['params']['message'])

    def test_action_test_connection_success(self):
        settings = self.settings_model.create({
            'is_connect_zendesk': True,
            'company_domain': 'testdomain',
            'zendesk_client_id': 'test_client_id',
            'zendesk_client_secret': 'test_client_secret',
            'zendesk_scope': 'read write',
        })
        with patch.object(self.api_cls, '_fetch_access_token') as mock_fetch, \
             patch.object(self.api_cls, '_request', return_value={'tickets': []}) as mock_req:
            res = settings.action_test_connection()
            mock_fetch.assert_called_once()
            mock_req.assert_called_once_with('GET', 'tickets.json', params={'per_page': 1})
            self.assertEqual(res['params']['type'], 'success')
            self.assertEqual(res['params']['title'], 'Connection Test Succeeded!')
