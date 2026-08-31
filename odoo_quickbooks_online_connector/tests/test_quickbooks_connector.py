# -*- coding: utf-8 -*-

import base64
from unittest.mock import Mock, patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestQuickbooksConnector(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.connector = cls.env['quickbooks.connector'].create({
            'name': 'Test QuickBooks',
            'quickbooks_realm': '1234567890',
            'quickbooks_client': 'client-id',
            'quickbooks_client_secret': 'client-secret',
            'quickbooks_access_token': 'access-token',
            'quickbooks_refresh_token': 'refresh-token',
            'quickbooks_access_token_url': 'https://oauth.example.test/token',
            'quickbooks_api_url': 'https://example.test/v3/company/',
            'authorised': True,
        })

    def test_onchange_quickbooks_mode_updates_api_url(self):
        self.connector.quickbooks_mode = 'sandbox'
        self.connector._onchange_quickbooks_mode()
        self.assertEqual(
            self.connector.quickbooks_api_url,
            'https://sandbox-quickbooks.api.intuit.com/v3/company/',
        )

        self.connector.quickbooks_mode = 'production'
        self.connector._onchange_quickbooks_mode()
        self.assertEqual(
            self.connector.quickbooks_api_url,
            'https://quickbooks.api.intuit.com/v3/company/',
        )

    def test_action_quickbook_auth_returns_url_action(self):
        self.env['ir.config_parameter'].sudo().set_param('web.base.url', 'http://localhost:8069')

        action = self.connector.action_quickbook_auth()

        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('client_id=client-id', action['url'])
        self.assertIn('redirect_uri=http://localhost:8069/quickbook_access', action['url'])
        self.assertEqual(action['target'], 'self')

    def test_get_import_query_returns_expected_headers(self):
        result = self.connector.get_import_query()

        self.assertEqual(result['url'], 'https://example.test/v3/company/1234567890')
        self.assertEqual(result['headers']['Authorization'], 'Bearer access-token')
        self.assertEqual(result['headers']['Accept'], 'application/json')
        self.assertEqual(result['headers']['Content-Type'], 'text/plain')

    def test_action_refresh_token_updates_tokens_on_success(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            'access_token': 'new-access',
            'refresh_token': 'new-refresh',
            'expires_in': 3600,
            'x_refresh_token_expires_in': 7200,
        }

        with patch(
            'odoo.addons.odoo_quickbooks_online_connector.models.quickbooks_connector.requests.post',
            return_value=response,
        ) as post_mock:
            action = self.connector.action_refresh_token()

        expected_basic = base64.b64encode(b'client-id:client-secret').decode('utf-8')
        post_mock.assert_called_once()
        self.assertIn(expected_basic, post_mock.call_args.kwargs['headers']['Authorization'])
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(self.connector.quickbooks_access_token, 'new-access')
        self.assertEqual(self.connector.quickbooks_refresh_token, 'new-refresh')

    def test_action_refresh_token_returns_error_when_params_missing(self):
        connector = self.env['quickbooks.connector'].create({
            'name': 'Incomplete QuickBooks',
            'quickbooks_realm': '1234567890',
            'quickbooks_client': 'client-id',
            'quickbooks_client_secret': 'client-secret',
            'quickbooks_refresh_token': False,
            'quickbooks_access_token_url': False,
            'quickbooks_api_url': 'https://example.test/v3/company/',
            'authorised': True,
        })

        action = connector.action_refresh_token()

        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertIn('token refresh parameters are not set', action['params']['message'].lower())
