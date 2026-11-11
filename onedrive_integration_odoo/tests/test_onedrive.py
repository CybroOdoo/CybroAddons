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
import base64
import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import tagged, TransactionCase
from ..hooks import uninstall_hook


@tagged('post_install', '-at_install')
class TestOneDriveIntegration(TransactionCase):
    """Test cases for OneDrive Integration module."""

    def setUp(self):
        super().setUp()
        self.ir_config = self.env['ir.config_parameter'].sudo()
        self.ir_config.set_str('onedrive_integration_odoo.client_id', 'test_client_id')
        self.ir_config.set_str('onedrive_integration_odoo.client_secret', 'test_client_secret')
        self.ir_config.set_str('onedrive_integration_odoo.tenant_id', 'test_tenant_id')
        self.ir_config.set_str('onedrive_integration_odoo.onedrive_folder', 'TestFolder')
        self.ir_config.set_bool('onedrive_integration_odoo.onedrive_button', True)
        self.ir_config.set_str('web.base.url', 'http://localhost:8069')

        self.dashboard_model = self.env['onedrive.dashboard']
        self.upload_model = self.env['upload.file']

    @patch('requests.post')
    def test_get_tokens_success(self, mock_post):
        """Test successfully retrieving tokens from authorization code."""
        mock_response = MagicMock()
        mock_response.content = b'{"access_token": "token123", "refresh_token": "refresh123", "expires_in": 3600}'
        mock_response.json.return_value = {
            'access_token': 'token123',
            'refresh_token': 'refresh123',
            'expires_in': 3600,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        initial_count = self.dashboard_model.search_count([])
        self.dashboard_model.get_tokens('auth_code_xyz')

        self.assertEqual(self.dashboard_model.search_count([]), initial_count + 1)
        latest = self.dashboard_model.search([], order='id desc', limit=1)
        self.assertEqual(latest.onedrive_access_token, 'token123')
        self.assertEqual(latest.onedrive_refresh_token, 'refresh123')
        self.assertTrue(latest.token_expiry_date)

    @patch('requests.post')
    def test_get_tokens_http_error(self, mock_post):
        """Test handling HTTPError when retrieving tokens."""
        mock_response = MagicMock()
        mock_response.content = b'{"error": "invalid_grant"}'
        mock_post.side_effect = requests.HTTPError(response=mock_response)

        with self.assertRaises(requests.HTTPError):
            self.dashboard_model.get_tokens('bad_auth_code')

    @patch('requests.post')
    def test_get_tokens_empty_response(self, mock_post):
        """Test retrieving tokens with empty response body."""
        mock_response = MagicMock()
        mock_response.content = b''
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        initial_count = self.dashboard_model.search_count([])
        self.dashboard_model.get_tokens('auth_code_empty')
        self.assertEqual(self.dashboard_model.search_count([]), initial_count)

    @patch('requests.post')
    def test_generate_onedrive_refresh_token_success(self, mock_post):
        """Test successfully refreshing an expired OneDrive token."""
        record = self.dashboard_model.create({
            'onedrive_access_token': 'old_token',
            'onedrive_refresh_token': 'old_refresh',
            'token_expiry_date': fields.Datetime.now() - timedelta(hours=2),
        })

        mock_response = MagicMock()
        mock_response.content = b'{"access_token": "new_token", "refresh_token": "new_refresh", "expires_in": 3600}'
        mock_response.json.return_value = {
            'access_token': 'new_token',
            'refresh_token': 'new_refresh',
            'expires_in': 3600,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        record.generate_onedrive_refresh_token()
        self.assertEqual(record.onedrive_access_token, 'new_token')
        self.assertEqual(record.onedrive_refresh_token, 'new_refresh')
        self.assertTrue(record.token_expiry_date > fields.Datetime.now())

    @patch('requests.post')
    def test_generate_onedrive_refresh_token_http_error(self, mock_post):
        """Test HTTP error when refreshing OneDrive token."""
        record = self.dashboard_model.create({
            'onedrive_access_token': 'old_token',
            'onedrive_refresh_token': 'old_refresh',
        })
        mock_response = MagicMock()
        mock_response.content = b'{"error": "invalid_grant"}'
        mock_post.side_effect = requests.HTTPError(response=mock_response)

        with self.assertRaises(requests.HTTPError):
            record.generate_onedrive_refresh_token()

    def test_action_synchronize_onedrive_no_record(self):
        """Test synchronization when no dashboard credentials record exists."""
        self.dashboard_model.search([]).unlink()
        result = self.dashboard_model.action_synchronize_onedrive()
        self.assertFalse(result)

    def test_action_synchronize_onedrive_no_folder(self):
        """Test synchronization when no folder name is configured."""
        self.dashboard_model.create({
            'onedrive_access_token': 'valid_token',
            'onedrive_refresh_token': 'valid_refresh',
            'token_expiry_date': fields.Datetime.now() + timedelta(hours=1),
        })
        self.ir_config.set_str('onedrive_integration_odoo.onedrive_folder', '')

        result = self.dashboard_model.action_synchronize_onedrive()
        self.assertFalse(result)

    @patch('requests.get')
    def test_action_synchronize_onedrive_api_error(self, mock_get):
        """Test synchronization when Microsoft Graph API returns an error."""
        self.dashboard_model.create({
            'onedrive_access_token': 'valid_token',
            'onedrive_refresh_token': 'valid_refresh',
            'token_expiry_date': fields.Datetime.now() + timedelta(hours=1),
        })

        mock_response = MagicMock()
        mock_response.content = json.dumps({
            'error': {
                'code': 'itemNotFound',
                'message': 'The resource could not be found.',
            }
        }).encode('utf-8')
        mock_get.return_value = mock_response

        result = self.dashboard_model.action_synchronize_onedrive()
        self.assertEqual(result, ['error', 'itemNotFound', 'The resource could not be found.'])

    @patch('requests.get')
    def test_action_synchronize_onedrive_success(self, mock_get):
        """Test synchronization successfully parses files from OneDrive folder."""
        self.dashboard_model.create({
            'onedrive_access_token': 'valid_token',
            'onedrive_refresh_token': 'valid_refresh',
            'token_expiry_date': fields.Datetime.now() + timedelta(hours=1),
        })

        payload = {
            'value': [
                {
                    'name': 'document.pdf',
                    '@microsoft.graph.downloadUrl': 'https://download.microsoft.com/file1',
                },
                {
                    'name': 'image.png',
                    '@microsoft.graph.downloadUrl': 'https://download.microsoft.com/file2',
                },
                {
                    'name': 'folder_without_url',
                },
            ]
        }
        mock_response = MagicMock()
        mock_response.content = json.dumps(payload).encode('utf-8')
        mock_response.json.return_value = payload
        mock_get.return_value = mock_response

        files = self.dashboard_model.action_synchronize_onedrive()
        self.assertEqual(len(files), 2)
        self.assertEqual(files['document.pdf'], 'https://download.microsoft.com/file1')
        self.assertEqual(files['image.png'], 'https://download.microsoft.com/file2')
        self.assertNotIn('folder_without_url', files)

    @patch('requests.post')
    def test_res_config_settings_auth_code_invalid_client(self, mock_post):
        """Test settings action raises UserError when credentials are invalid."""
        mock_response = MagicMock()
        mock_response.content = b'{"error": "invalid_client", "error_description": "Invalid secret"}'
        mock_response.json.return_value = {
            'error': 'invalid_client',
            'error_description': 'Invalid secret',
        }
        mock_post.return_value = mock_response

        settings = self.env['res.config.settings'].create({
            'onedrive_client': 'bad_client',
            'onedrive_client_secret': 'bad_secret',
            'onedrive_tenant_id': 'bad_tenant',
        })

        with self.assertRaises(UserError):
            settings.action_get_onedrive_auth_code()

    @patch('requests.post')
    def test_res_config_settings_auth_code_success(self, mock_post):
        """Test settings action returns OAuth redirect URL on valid setup."""
        mock_response = MagicMock()
        mock_response.content = b'{"token_type": "Bearer", "access_token": "app_token"}'
        mock_response.json.return_value = {'token_type': 'Bearer', 'access_token': 'app_token'}
        mock_post.return_value = mock_response

        settings = self.env['res.config.settings'].create({
            'onedrive_client': 'valid_client',
            'onedrive_client_secret': 'valid_secret',
            'onedrive_tenant_id': 'valid_tenant',
        })

        action = settings.action_get_onedrive_auth_code()
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('target'), 'self')
        self.assertIn('https://login.microsoftonline.com/common/oauth2/v2.0/authorize', action.get('url', ''))
        self.assertIn('valid_client', action.get('url', ''))

    def test_upload_file_no_file(self):
        """Test upload wizard raises UserError when no file is selected."""
        wizard = self.upload_model.create({
            'file_name': 'test.txt',
        })
        with self.assertRaises(UserError):
            wizard.action_upload_file()

    def test_upload_file_no_credentials(self):
        """Test upload wizard raises UserError when token or folder is missing."""
        self.dashboard_model.search([]).unlink()
        wizard = self.upload_model.create({
            'file': base64.b64encode(b'Hello World').decode('ascii'),
            'file_name': 'test.txt',
        })
        with self.assertRaises(UserError):
            wizard.action_upload_file()

    @patch('requests.put')
    def test_upload_file_success(self, mock_put):
        """Test successful file upload to OneDrive."""
        self.dashboard_model.create({
            'onedrive_access_token': 'valid_token',
            'onedrive_refresh_token': 'valid_refresh',
            'token_expiry_date': fields.Datetime.now() + timedelta(hours=1),
        })

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_put.return_value = mock_response

        wizard = self.upload_model.create({
            'file': base64.b64encode(b'Hello OneDrive').decode('ascii'),
            'file_name': 'hello.txt',
        })

        result = wizard.action_upload_file()
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'display_notification')
        self.assertEqual(result.get('params', {}).get('type'), 'success')

    @patch('requests.put')
    def test_upload_file_api_failure(self, mock_put):
        """Test upload wizard raises UserError when upload returns error status."""
        self.dashboard_model.create({
            'onedrive_access_token': 'valid_token',
            'onedrive_refresh_token': 'valid_refresh',
            'token_expiry_date': fields.Datetime.now() + timedelta(hours=1),
        })

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = 'Access Denied'
        mock_put.return_value = mock_response

        wizard = self.upload_model.create({
            'file': base64.b64encode(b'Content').decode('ascii'),
            'file_name': 'doc.txt',
        })

        with self.assertRaises(UserError):
            wizard.action_upload_file()

    @patch('requests.put')
    def test_upload_file_network_exception(self, mock_put):
        """Test upload wizard raises UserError when network connection fails."""
        self.dashboard_model.create({
            'onedrive_access_token': 'valid_token',
            'onedrive_refresh_token': 'valid_refresh',
            'token_expiry_date': fields.Datetime.now() + timedelta(hours=1),
        })

        mock_put.side_effect = requests.RequestException('Timeout connecting to host')

        wizard = self.upload_model.create({
            'file': base64.b64encode(b'Content').decode('ascii'),
            'file_name': 'doc.txt',
        })

        with self.assertRaises(UserError):
            wizard.action_upload_file()

    def test_uninstall_hook(self):
        """Test that uninstall_hook cleanly removes system parameters."""
        self.ir_config.set_str('onedrive_integration_odoo.client_id', 'to_delete')
        self.ir_config.set_str('onedrive_integration_odoo.client_secret', 'to_delete')
        self.ir_config.set_str('onedrive_integration_odoo.tenant_id', 'to_delete')
        self.ir_config.set_str('onedrive_integration_odoo.onedrive_folder', 'to_delete')
        self.ir_config.set_bool('onedrive_integration_odoo.onedrive_button', True)

        uninstall_hook(self.env)

        keys = [
            'onedrive_integration_odoo.client_id',
            'onedrive_integration_odoo.client_secret',
            'onedrive_integration_odoo.tenant_id',
            'onedrive_integration_odoo.onedrive_folder',
            'onedrive_integration_odoo.onedrive_button',
        ]
        remaining = self.ir_config.search_count([('key', 'in', keys)])
        self.assertEqual(remaining, 0)

