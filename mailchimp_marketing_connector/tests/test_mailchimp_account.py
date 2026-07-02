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

from types import ModuleType
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestMailchimpAccount(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls.env['mailchimp.account'].create({
            'name': 'Mailchimp',
            'api_key': 'abc-us1',
        })

    def test_connect_mailchimp_missing_dependency(self):
        real_import = __import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'mailchimp_marketing' or name.startswith('mailchimp_marketing.'):
                raise ImportError()
            return real_import(name, globals, locals, fromlist, level)

        with patch('builtins.__import__', side_effect=fake_import):
            action = self.account.connect_mailchimp()

        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['title'], 'Missing Dependency')
        self.assertFalse(self.account.is_auth_success)

    def test_connect_mailchimp_success(self):
        class FakePing:
            def get(self):
                return True

        class FakeClient:
            def __init__(self):
                self.config = None
                self.ping = FakePing()

            def set_config(self, config):
                self.config = config

        class FakeApiClientError(Exception):
            def __init__(self, text):
                self.text = text

        fake_client_module = ModuleType('mailchimp_marketing')
        fake_client_module.Client = FakeClient
        fake_api_client_module = ModuleType('mailchimp_marketing.api_client')
        fake_api_client_module.ApiClientError = FakeApiClientError

        with patch.dict(
            'sys.modules',
            {
                'mailchimp_marketing': fake_client_module,
                'mailchimp_marketing.api_client': fake_api_client_module,
            },
            clear=False,
        ):
            action = self.account.connect_mailchimp()

        self.account.invalidate_recordset(['is_auth_success'])
        self.assertEqual(action['params']['title'], 'Success')
        self.assertTrue(self.account.is_auth_success)

    def test_connect_mailchimp_api_error(self):
        class FakePing:
            def get(self):
                raise FakeApiClientError('Authentication failed')

        class FakeClient:
            def __init__(self):
                self.ping = FakePing()

            def set_config(self, config):
                self.config = config

        class FakeApiClientError(Exception):
            def __init__(self, text):
                self.text = text

        fake_client_module = ModuleType('mailchimp_marketing')
        fake_client_module.Client = FakeClient
        fake_api_client_module = ModuleType('mailchimp_marketing.api_client')
        fake_api_client_module.ApiClientError = FakeApiClientError

        with patch.dict(
            'sys.modules',
            {
                'mailchimp_marketing': fake_client_module,
                'mailchimp_marketing.api_client': fake_api_client_module,
            },
            clear=False,
        ):
            action = self.account.connect_mailchimp()

        self.assertEqual(action['params']['title'], 'Authentication Failed')
        self.assertEqual(action['params']['message'], 'Authentication failed')
        self.assertFalse(self.account.is_auth_success)
