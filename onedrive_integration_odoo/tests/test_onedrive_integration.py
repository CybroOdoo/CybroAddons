# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock
from odoo.exceptions import UserError
import base64

class TestOnedriveIntegration(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param('web.base.url', 'http://localhost:8069')
        self.env['ir.config_parameter'].sudo().set_param('onedrive_integration_odoo.client_id', 'test_client_id')
        self.env['ir.config_parameter'].sudo().set_param('onedrive_integration_odoo.client_secret', 'test_client_secret')
        self.env['ir.config_parameter'].sudo().set_param('onedrive_integration_odoo.tenant_id', 'test_tenant_id')
        self.env['ir.config_parameter'].sudo().set_param('onedrive_integration_odoo.onedrive_folder', 'TestFolder')
        
        self.ConfigSettings = self.env['res.config.settings']
        self.OnedriveDashboard = self.env['onedrive.dashboard']
        self.UploadFile = self.env['upload.file']

    @patch('requests.post')
    def test_action_get_onedrive_auth_code(self, mock_post):
        """Test the OAuth code generation logic"""
        mock_response = MagicMock()
        mock_response.content = b'{"access_token": "test_token"}'
        mock_response.json.return_value = {"access_token": "test_token"}
        mock_post.return_value = mock_response

        settings = self.ConfigSettings.create({})
        action = settings.action_get_onedrive_auth_code()
        
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertIn('https://login.microsoftonline.com/common/oauth2/v2.0/authorize', action.get('url'))
        self.assertIn('client_id=test_client_id', action.get('url'))

    @patch('requests.post')
    def test_action_get_onedrive_auth_code_error(self, mock_post):
        """Test behavior when the OAuth request fails"""
        mock_response = MagicMock()
        mock_response.content = b'{"error": "invalid_client"}'
        mock_response.json.return_value = {"error": "invalid_client"}
        mock_post.return_value = mock_response

        settings = self.ConfigSettings.create({})
        with self.assertRaisesRegex(UserError, "Error 'invalid_client': Please check the credentials."):
            settings.action_get_onedrive_auth_code()

    @patch('requests.post')
    def test_get_tokens(self, mock_post):
        """Test getting tokens using auth code"""
        mock_response = MagicMock()
        mock_response.content = b'{"expires_in": 3600, "access_token": "new_access", "refresh_token": "new_refresh"}'
        mock_response.json.return_value = {"expires_in": 3600, "access_token": "new_access", "refresh_token": "new_refresh"}
        mock_post.return_value = mock_response

        self.OnedriveDashboard.get_tokens('test_auth_code')
        
        token_record = self.OnedriveDashboard.search([], limit=1, order='id desc')
        self.assertTrue(token_record)
        self.assertEqual(token_record.onedrive_access_token, 'new_access')
        self.assertEqual(token_record.onedrive_refresh_token, 'new_refresh')
        self.assertTrue(token_record.token_expiry_date)

    @patch('requests.post')
    def test_generate_onedrive_refresh_token(self, mock_post):
        """Test token refresh logic"""
        token_record = self.OnedriveDashboard.create({
            'onedrive_access_token': 'old_access',
            'onedrive_refresh_token': 'old_refresh',
            'token_expiry_date': '2020-01-01 00:00:00',
        })

        mock_response = MagicMock()
        mock_response.content = b'{"expires_in": 3600, "access_token": "refreshed_access", "refresh_token": "refreshed_refresh"}'
        mock_response.json.return_value = {"expires_in": 3600, "access_token": "refreshed_access", "refresh_token": "refreshed_refresh"}
        mock_post.return_value = mock_response

        token_record.generate_onedrive_refresh_token()
        
        self.assertEqual(token_record.onedrive_access_token, 'refreshed_access')
        self.assertEqual(token_record.onedrive_refresh_token, 'refreshed_refresh')

    @patch('requests.get')
    def test_action_synchronize_onedrive(self, mock_get):
        """Test synchronizing files from OneDrive"""
        token_record = self.OnedriveDashboard.create({
            'onedrive_access_token': 'valid_access_token',
            'onedrive_refresh_token': 'valid_refresh_token',
            'token_expiry_date': '2099-01-01 00:00:00',
        })

        mock_response = MagicMock()
        mock_response.content = b'{"value": [{"name": "test.txt", "@microsoft.graph.downloadUrl": "http://download.url"}]}'
        mock_response.json.return_value = {"value": [{"name": "test.txt", "@microsoft.graph.downloadUrl": "http://download.url"}]}
        mock_get.return_value = mock_response

        result = token_record.action_synchronize_onedrive()
        
        self.assertIsInstance(result, dict)
        self.assertIn('test.txt', result)
        self.assertEqual(result['test.txt'], 'http://download.url')

    @patch('requests.put')
    def test_action_upload_file(self, mock_put):
        """Test uploading a file"""
        token_record = self.OnedriveDashboard.create({
            'onedrive_access_token': 'valid_access_token',
            'onedrive_refresh_token': 'valid_refresh_token',
            'token_expiry_date': '2099-01-01 00:00:00',
        })
        
        wizard = self.UploadFile.create({
            'file': base64.b64encode(b'Test Content'),
            'file_name': 'test_upload.txt'
        })
        
        # Attachment needs to be correctly identified by the upload_file action_upload_file method
        attachment = self.env['ir.attachment'].create({
            'name': 'test_upload.txt',
            'datas': wizard.file,
            'res_model': 'upload.file',
            'res_id': wizard.id
        })

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_put.return_value = mock_response

        result = wizard.action_upload_file()
        
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'display_notification')
