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

from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.odoo_zendesk_connector.models.zendesk_api import (
    ODOO_TO_ZENDESK_PRIORITY,
    ZENDESK_TO_ODOO_PRIORITY,
)


@tagged('post_install', '-at_install')
class TestZendeskApi(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.api = cls.env['zendesk.api']
        cls.api_cls = type(cls.api)
        cls.params = cls.env['ir.config_parameter'].sudo()

    def setUp(self):
        super().setUp()
        self.api._set_param('is_connect_zendesk', 'True')
        self.api._set_param('company_domain', 'testdomain')
        self.api._set_param('client_id', 'client_123')
        self.api._set_param('client_secret', 'secret_456')
        self.api._set_param('scope', 'read write')
        self.api._clear_token()

    def test_is_connected(self):
        self.api._set_param('is_connect_zendesk', 'True')
        self.assertTrue(self.api._is_connected())
        self.api._set_param('is_connect_zendesk', 'False')
        self.assertFalse(self.api._is_connected())

    def test_get_config_disabled(self):
        self.api._set_param('is_connect_zendesk', 'False')
        with self.assertRaises(UserError) as cm:
            self.api._get_config()
        self.assertIn("Zendesk connection is disabled", str(cm.exception))

    def test_param_get_and_set(self):
        self.api._set_param('custom_key', 'custom_value')
        self.assertEqual(self.api._get_param('custom_key'), 'custom_value')
        self.api._set_param('custom_key', False)
        self.assertFalse(self.api._get_param('custom_key'))

    def test_get_config_success(self):
        config = self.api._get_config()
        self.assertEqual(config['domain'], 'testdomain')
        self.assertEqual(config['client_id'], 'client_123')
        self.assertEqual(config['client_secret'], 'secret_456')
        self.assertEqual(config['scope'], 'read write')

    def test_get_config_missing_fields(self):
        self.api._set_param('client_secret', '')
        with self.assertRaises(UserError) as cm:
            self.api._get_config()
        self.assertIn('OAuth Client Secret', str(cm.exception))

        self.api._set_param('domain', '')
        self.api._set_param('company_domain', '')
        self.api._set_param('client_id', '')
        with self.assertRaises(UserError) as cm:
            self.api._get_config()
        self.assertIn('Company Domain', str(cm.exception))

    def test_base_url_formatting(self):
        self.assertEqual(self.api._base_url('mycompany'), 'https://mycompany.zendesk.com')
        self.assertEqual(self.api._base_url('https://mycompany.zendesk.com/'), 'https://mycompany.zendesk.com')
        self.assertEqual(self.api._base_url('http://mycompany.zendesk.com'), 'https://mycompany.zendesk.com')
        self.assertEqual(self.api._base_url(), 'https://testdomain.zendesk.com')

    @patch('odoo.addons.odoo_zendesk_connector.models.zendesk_api.requests.post')
    def test_fetch_access_token_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_token_abc',
            'expires_in': 3600,
        }
        mock_post.return_value = mock_response

        token = self.api._fetch_access_token()
        self.assertEqual(token, 'test_token_abc')
        self.assertEqual(self.api._get_param('access_token'), 'test_token_abc')
        self.assertTrue(self.api._get_param('token_expiry'))

    @patch('odoo.addons.odoo_zendesk_connector.models.zendesk_api.requests.post')
    def test_fetch_access_token_connection_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError('Network unreachable')
        with self.assertRaises(UserError) as cm:
            self.api._fetch_access_token()
        self.assertIn('Could not reach Zendesk', str(cm.exception))

    @patch('odoo.addons.odoo_zendesk_connector.models.zendesk_api.requests.post')
    def test_fetch_access_token_refused(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "invalid_client"}'
        mock_post.return_value = mock_response

        with self.assertRaises(UserError) as cm:
            self.api._fetch_access_token()
        self.assertIn('Zendesk refused the OAuth request', str(cm.exception))

    @patch('odoo.addons.odoo_zendesk_connector.models.zendesk_api.requests.post')
    def test_fetch_access_token_missing_token_in_body(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'expires_in': 3600}
        mock_post.return_value = mock_response

        with self.assertRaises(UserError) as cm:
            self.api._fetch_access_token()
        self.assertIn('Zendesk did not return an access token', str(cm.exception))

    def test_get_access_token_caching(self):
        # Set a future expiry
        future_time = fields.Datetime.now() + timedelta(hours=2)
        self.api._set_param('access_token', 'cached_token_xyz')
        self.api._set_param('token_expiry', fields.Datetime.to_string(future_time))

        with patch.object(self.api_cls, '_fetch_access_token') as mock_fetch:
            token = self.api._get_access_token()
            self.assertEqual(token, 'cached_token_xyz')
            mock_fetch.assert_not_called()

        # Set an expired token
        past_time = fields.Datetime.now() - timedelta(hours=1)
        self.api._set_param('token_expiry', fields.Datetime.to_string(past_time))
        with patch.object(self.api_cls, '_fetch_access_token', return_value='renewed_token') as mock_fetch:
            token = self.api._get_access_token()
            self.assertEqual(token, 'renewed_token')
            mock_fetch.assert_called_once()

    def test_clear_token(self):
        self.api._set_param('access_token', 'token_to_clear')
        self.api._set_param('token_expiry', '2026-11-13 12:00:00')
        self.api._clear_token()
        self.assertFalse(self.api._get_param('access_token'))
        self.assertFalse(self.api._get_param('token_expiry'))

    @patch('odoo.addons.odoo_zendesk_connector.models.zendesk_api.requests.request')
    def test_raw_request_relative_and_absolute(self, mock_req):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"ok": true}'
        mock_req.return_value = mock_resp

        with patch.object(self.api_cls, '_get_access_token', return_value='bearer_token'):
            res = self.api._raw_request('GET', 'tickets.json', headers={'X-Custom': 'val'})
            self.assertEqual(res, mock_resp)
            mock_req.assert_called_with(
                'GET',
                'https://testdomain.zendesk.com/api/v2/tickets.json',
                headers={'Content-Type': 'application/json', 'Authorization': 'Bearer bearer_token', 'X-Custom': 'val'},
                timeout=60,
            )

            # Valid Absolute URL under _base_url()
            self.api._raw_request('GET', 'https://testdomain.zendesk.com/api/v2/next.json')
            mock_req.assert_called_with(
                'GET',
                'https://testdomain.zendesk.com/api/v2/next.json',
                headers={'Content-Type': 'application/json', 'Authorization': 'Bearer bearer_token'},
                timeout=60,
            )

            # Untrusted host raises UserError to prevent token leakage
            with self.assertRaises(UserError) as cm:
                self.api._raw_request('GET', 'https://other.zendesk.com/api/v2/next.json')
            self.assertIn('Invalid Zendesk endpoint', str(cm.exception))

    @patch('odoo.addons.odoo_zendesk_connector.models.zendesk_api.requests.request')
    def test_raw_request_connection_error(self, mock_req):
        mock_req.side_effect = requests.exceptions.Timeout('Timeout reached')
        with patch.object(self.api_cls, '_get_access_token', return_value='tok'):
            with self.assertRaises(UserError) as cm:
                self.api._raw_request('GET', 'tickets.json')
            self.assertIn('Could not reach Zendesk', str(cm.exception))

    @patch('odoo.addons.odoo_zendesk_connector.models.zendesk_api.requests.request')
    def test_raw_request_token_retry_on_401(self, mock_req):
        resp_401 = MagicMock()
        resp_401.status_code = 401
        resp_401.text = '{"error": "invalid_token"}'

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.text = '{"success": true}'

        mock_req.side_effect = [resp_401, resp_200]

        with patch.object(self.api_cls, '_get_access_token', side_effect=['old_token', 'new_token']):
            with patch.object(self.api_cls, '_clear_token') as mock_clear:
                res = self.api._raw_request('GET', 'tickets.json')
                self.assertEqual(res, resp_200)
                mock_clear.assert_called_once()
                self.assertEqual(mock_req.call_count, 2)

    def test_request_success_with_json_and_empty(self):
        resp = MagicMock()
        resp.ok = True
        resp.content = b'{"tickets": [1, 2]}'
        resp.json.return_value = {'tickets': [1, 2]}
        with patch.object(self.api_cls, '_raw_request', return_value=resp):
            data = self.api._request('GET', 'tickets.json')
            self.assertEqual(data, {'tickets': [1, 2]})

        # Empty content (204 No Content)
        resp_empty = MagicMock()
        resp_empty.ok = True
        resp_empty.content = b''
        with patch.object(self.api_cls, '_raw_request', return_value=resp_empty):
            data = self.api._request('DELETE', 'tickets/123.json')
            self.assertEqual(data, {})

    def test_request_failure_raises_user_error(self):
        resp_err = MagicMock()
        resp_err.ok = False
        resp_err.status_code = 404
        resp_err.content = b'{"error": "RecordNotFound"}'
        resp_err.json.return_value = {'error': 'RecordNotFound'}
        with patch.object(self.api_cls, '_raw_request', return_value=resp_err):
            with self.assertRaises(UserError) as cm:
                self.api._request('GET', 'tickets/9999.json')
            self.assertIn('RecordNotFound', str(cm.exception))

    def test_error_text_variations(self):
        resp = MagicMock()
        # 1. Error dictionary with message
        resp.json.return_value = {'error': {'message': 'Custom error message'}}
        self.assertEqual(self.api._error_text(resp), 'Custom error message')

        # 2. Error dictionary with title
        resp.json.return_value = {'error': {'title': 'Forbidden Error'}}
        self.assertEqual(self.api._error_text(resp), 'Forbidden Error')

        # 3. Description present
        resp.json.return_value = {'description': 'Detailed issue description'}
        self.assertEqual(self.api._error_text(resp), 'Detailed issue description')

        # 4. Error string
        resp.json.return_value = {'error': 'Simple error string'}
        self.assertEqual(self.api._error_text(resp), 'Simple error string')

        # 5. Non-JSON text
        resp.json.side_effect = ValueError('Not JSON')
        resp.text = 'Raw 502 Bad Gateway text'
        self.assertEqual(self.api._error_text(resp), 'Raw 502 Bad Gateway text')

    def test_find_or_create_user(self):
        # Missing email raises UserError
        with self.assertRaises(UserError) as cm:
            self.api._find_or_create_user('John Doe', '')
        self.assertIn('email is required', str(cm.exception))

        # Existing user found
        with patch.object(self.api_cls, '_request', return_value={'users': [{'id': 101, 'name': 'John'}]}) as mock_req:
            uid = self.api._find_or_create_user('John', 'john@example.com')
            self.assertEqual(uid, 101)
            mock_req.assert_called_once_with('GET', 'users/search.json', params={'query': 'email:john@example.com'})

        # User not found -> created
        with patch.object(self.api_cls, '_request', side_effect=[
            {'users': []},
            {'user': {'id': 202, 'name': 'Jane', 'email': 'jane@example.com'}},
        ]) as mock_req:
            uid = self.api._find_or_create_user('Jane', 'jane@example.com')
            self.assertEqual(uid, 202)
            self.assertEqual(mock_req.call_count, 2)

    def test_notify(self):
        notif = self.api.notify('Test Title', 'Test Message', notif_type='success', sticky=True)
        self.assertEqual(notif['type'], 'ir.actions.client')
        self.assertEqual(notif['tag'], 'display_notification')
        self.assertEqual(notif['params']['title'], 'Test Title')
        self.assertEqual(notif['params']['message'], 'Test Message')
        self.assertEqual(notif['params']['type'], 'success')
        self.assertTrue(notif['params']['sticky'])

    def test_priority_mappings(self):
        self.assertEqual(ODOO_TO_ZENDESK_PRIORITY['1'], 'low')
        self.assertEqual(ODOO_TO_ZENDESK_PRIORITY['2'], 'normal')
        self.assertEqual(ODOO_TO_ZENDESK_PRIORITY['3'], 'high')
        self.assertEqual(ODOO_TO_ZENDESK_PRIORITY['4'], 'urgent')
        self.assertEqual(ZENDESK_TO_ODOO_PRIORITY['low'], '1')
        self.assertEqual(ZENDESK_TO_ODOO_PRIORITY['urgent'], '4')
