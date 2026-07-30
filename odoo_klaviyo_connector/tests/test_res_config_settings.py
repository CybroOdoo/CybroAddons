# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import unittest.mock
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResConfigSettings, cls).setUpClass()
        cls.config = cls.env['res.config.settings'].create({
            'api_key': 'test_klaviyo_api_key',
            'import_data': True,
            'export_data': True,
        })
        
        cls.mailing_list = cls.env['mailing.list'].create({
            'name': 'Test List'
        })
        
        cls.contact = cls.env['mailing.contact'].create({
            'name': 'Test Contact',
            'email': 'test@example.com'
        })
        cls.mailing_list.write({'contact_ids': [(4, cls.contact.id)]})

    @unittest.mock.patch('requests.request')
    def test_action_test_connection_success(self, mock_request):
        """Test successful connection testing."""
        mock_response = unittest.mock.MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        notification = self.config.action_test_connection()
        self.assertEqual(notification['params']['type'], 'success')
        self.assertIn('Connection to Klaviyo is successful', notification['params']['message'])

    @unittest.mock.patch('requests.request')
    def test_action_test_connection_failure(self, mock_request):
        """Test failed connection testing."""
        mock_response = unittest.mock.MagicMock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        notification = self.config.action_test_connection()
        self.assertEqual(notification['params']['type'], 'danger')

    def test_action_test_connection_no_api_key(self):
        """Test connection testing without API key raises ValidationError."""
        self.config.api_key = False
        with self.assertRaises(ValidationError):
            self.config.action_test_connection()

    def test_action_notify(self):
        """Test notify structure."""
        notification = self.config.action_notify(True)
        self.assertEqual(notification['type'], 'ir.actions.client')
        self.assertEqual(notification['tag'], 'display_notification')
        self.assertEqual(notification['params']['type'], 'success')

    @unittest.mock.patch('requests.post')
    def test_get_list_response(self, mock_post):
        """Test getting list response from klaviyo."""
        mock_response = unittest.mock.MagicMock()
        mock_post.return_value = mock_response
        
        headers = {'Authorization': 'Klaviyo-API-Key test'}
        res = self.config.get_list_response(self.mailing_list, 'http://test.url', headers)
        self.assertEqual(res, mock_response)
        mock_post.assert_called_once()

    @unittest.mock.patch('requests.request')
    def test_get_klaviyo_members(self, mock_request):
        """Test getting members from klaviyo."""
        mock_response = unittest.mock.MagicMock()
        mock_request.return_value = mock_response
        
        res = self.config.get_klaviyo_members('test_user_id')
        self.assertEqual(res, mock_response)
        mock_request.assert_called_once()

    def test_create_mailing_list_and_contacts(self):
        """Test creating odoo records from klaviyo response."""
        mock_response = unittest.mock.MagicMock()
        mock_response.json.return_value = {
            'records': [{'id': 'c1', 'email': 'c1@test.com'}]
        }
        klaviyo_list = {'id': 'k1', 'attributes': {'name': 'Imported List'}}
        
        self.config.create_mailing_list_and_contacts(mock_response, klaviyo_list)
        
        new_list = self.env['mailing.list'].search([('klaviyo_id', '=', 'k1')])
        self.assertTrue(new_list)
        self.assertEqual(new_list.name, 'Imported List')
        self.assertEqual(len(new_list.contact_ids), 1)
        self.assertEqual(new_list.contact_ids[0].email, 'c1@test.com')

    @unittest.mock.patch('requests.request')
    @unittest.mock.patch('requests.post')
    def test_export_mailing_list(self, mock_post, mock_request):
        """Test exporting a mailing list to klaviyo."""
        mock_list_response = unittest.mock.MagicMock()
        mock_list_response.status_code = 201
        mock_list_response.json.return_value = {'data': {'id': 'k_new_list'}}
        
        mock_profile_response = unittest.mock.MagicMock()
        mock_profile_response.status_code = 201
        mock_profile_response.json.return_value = {'data': {'id': 'k_new_profile'}}
        
        # We need mock_post to return list_response on first call, profile_response on second call
        mock_post.side_effect = [mock_list_response, mock_profile_response]
        
        mock_rel_response = unittest.mock.MagicMock()
        mock_rel_response.status_code = 200
        mock_request.return_value = mock_rel_response
        
        headers = {'Authorization': 'Klaviyo-API-Key test'}
        self.config.export_mailing_list(self.mailing_list, headers)
        
        self.assertEqual(self.mailing_list.klaviyo_id, 'k_new_list')
        mock_request.assert_called_once()
        self.assertEqual(mock_post.call_count, 2)

    @unittest.mock.patch('odoo.addons.odoo_klaviyo_connector.models.res_config_settings.ResConfigSettings.export_mailing_list')
    @unittest.mock.patch('odoo.addons.odoo_klaviyo_connector.models.res_config_settings.ResConfigSettings.create_mailing_list_and_contacts')
    @unittest.mock.patch('odoo.addons.odoo_klaviyo_connector.models.res_config_settings.ResConfigSettings.get_klaviyo_members')
    @unittest.mock.patch('odoo.addons.odoo_klaviyo_connector.models.res_config_settings.ResConfigSettings.action_test_connection')
    def test_action_execute_operation(self, mock_test_connection, mock_get_members, mock_create, mock_export):
        """Test the main execute operation for import and export."""
        mock_response = unittest.mock.MagicMock()
        mock_response.json.return_value = {
            'data': [{'id': 'klaviyo_list_1', 'attributes': {'name': 'Remote List'}}]
        }
        mock_test_connection.return_value = mock_response
        
        notification = self.config.action_execute_operation()
        
        self.assertEqual(notification['type'], 'ir.actions.client')
        self.assertIn('Successfully imported', notification['params']['message'])
        
        mock_test_connection.assert_called_once_with(get_data=True)
        mock_get_members.assert_called_once_with(user_id='klaviyo_list_1')
        mock_create.assert_called_once()
        mock_export.assert_called_once()
