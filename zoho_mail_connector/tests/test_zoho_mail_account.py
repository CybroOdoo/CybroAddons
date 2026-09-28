# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3 for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock
from odoo.exceptions import UserError
from odoo import fields
import datetime

class TestZohoMailAccount(TransactionCase):

    def setUp(self):
        """Set up a Zoho Mail account test record."""
        super(TestZohoMailAccount, self).setUp()
        self.account = self.env['zoho.mail.account'].create({
            'name': 'Test Account',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'zoho_region': 'com',
            'refresh_token': 'dummy_refresh_token',
        })

    def test_compute_redirect_uri(self):
        """Test that the OAuth redirect URI is computed correctly."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('web.base.url', 'http://localhost:8069')
        self.assertEqual(
            self.account.redirect_uri,
            'http://localhost:8069/zoho_mail/oauth/callback'
        )

    def test_set_and_compute_connection_error(self):
        """Test setting and computing the connection error field."""
        self.account._set_connection_error("Test Error")
        # Trigger compute
        self.account._compute_connection_error()
        self.assertEqual(self.account.connection_error, "Test Error")

        self.account._set_connection_error(False)
        self.account._compute_connection_error()
        self.assertFalse(self.account.connection_error)

    def test_action_connect(self):
        """Test that the OAuth connection action generates the correct URL."""
        action = self.account.action_connect()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('https://accounts.zoho.com/oauth/v2/auth', action['url'])
        self.assertIn('client_id=test_client_id', action['url'])
        self.assertIn('response_type=code', action['url'])

    @patch('odoo.addons.zoho_mail_connector.models.zoho_mail_account.requests.post')
    def test_generate_access_token_success(self, mock_post):
        """Test successful generation and storage of an access token."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'expires_in': 3600
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        token = self.account._generate_access_token()
        self.assertEqual(token, 'new_access_token')
        self.assertEqual(self.account.access_token, 'new_access_token')
        self.assertTrue(self.account.token_expiry)

    @patch('odoo.addons.zoho_mail_connector.models.zoho_mail_account.requests.post')
    def test_generate_access_token_failure(self, mock_post):
        """Test that access token generation raises UserError on failure."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'error': 'invalid_client'}
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        with self.assertRaises(UserError):
            self.account._generate_access_token()

    @patch('odoo.addons.zoho_mail_connector.models.zoho_mail_account.requests.get')
    def test_test_connection_success(self, mock_get):
        """Test a successful Zoho Mail connection."""
        self.account.access_token = 'valid_token'
        self.account.token_expiry = fields.Datetime.now() + datetime.timedelta(hours=1)

        mock_response = MagicMock()
        mock_response.json.return_value = {'data': [{'accountId': '123'}]}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.account.test_connection()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'success')

    @patch('odoo.addons.zoho_mail_connector.models.zoho_mail_account.requests.get')
    def test_action_fetch_folders(self, mock_get):
        """Test synchronizing inbox messages from Zoho Mail."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {'folderName': 'Inbox', 'folderId': 'inbox_123'},
                {'folderName': 'Sent', 'folderId': 'sent_456'}
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        self.account.action_fetch_folders('dummy_token')
        self.assertEqual(self.account.inbox_folder_id, 'inbox_123')
        self.assertEqual(self.account.sent_folder_id, 'sent_456')


    @patch('odoo.addons.zoho_mail_connector.models.zoho_mail_account.requests.get')
    @patch('odoo.addons.zoho_mail_connector.models.zoho_mail_account.ZohoMailAccount._generate_access_token')
    def test_action_sync_inbox(self, mock_generate_token, mock_get):
        """Test sending an email through Zoho Mail."""
        mock_generate_token.return_value = 'dummy_token'
        self.account.inbox_folder_id = 'inbox_123'
        
        # Mock requests.get for messages/view
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {
                    'messageId': 'msg_1',
                    'subject': 'Test Subject',
                    'fromAddress': 'sender@test.com',
                    'toAddress': 'receiver@test.com',
                    'receivedTime': 1609459200000,
                    'hasAttachment': 0
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Need to also patch _get_message_content because it will be called internally?
        # Actually it's easier to mock it directly, but let's patch it
        with patch.object(self.env['zoho.mail.account'], '_get_message_content', return_value='Test Body'):
            with patch.object(self.env['zoho.mail.account'], '_process_inline_images', return_value='Test Body'):
                result = self.account.action_sync_inbox()
        
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['params']['type'], 'success')
        
        # Check if record was created
        mail = self.env['zoho.mail.message'].search([('message_id', '=', 'msg_1')])
        self.assertTrue(mail)
        self.assertEqual(mail.subject, 'Test Subject')
        self.assertEqual(mail.mail_type, 'inbox')

    @patch('odoo.addons.zoho_mail_connector.models.zoho_mail_account.requests.post')
    @patch('odoo.addons.zoho_mail_connector.models.zoho_mail_account.ZohoMailAccount._generate_access_token')
    def test_send_mail(self, mock_generate_token, mock_post):
        """Test sending an email using Zoho."""
        mock_generate_token.return_value = 'dummy_token'
        self.account.email_address = 'test@zohomail.com'
        self.account.account_id = '123'
        
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': {'messageId': 'new_msg_1'}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = self.account.send_mail(
            to_address='receiver@zohomail.com',
            subject='Outgoing Subject',
            body='Hello!'
        )
        
        self.assertIn('data', result)
        self.assertEqual(result['data']['messageId'], 'new_msg_1')
