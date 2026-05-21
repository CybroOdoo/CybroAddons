# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#############################################################################
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase

class TestMailerCloudSync(TransactionCase):

    def setUp(self):
        super(TestMailerCloudSync, self).setUp()
        self.SyncModel = self.env['mailer.cloud.api.sync']
        self.sync_record = self.SyncModel.create({
            'api_key': 'test_api_key',
            'name': 'Test Sync',
            'active': True
        })

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_sync(self, mock_request):
        """Test connection and data retrieval from Mailercloud."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'email': 'test@example.com',
                'name': 'Test User',
                'plan': 'Free',
                'remaining_contacts': 100,
                'total_contacts': 1000,
                'used_contacts': 900
            }
        }
        mock_request.return_value = mock_response
        
        with patch.object(type(self.SyncModel), 'get_list'), \
             patch.object(type(self.SyncModel), 'get_properties'):
            self.sync_record.action_sync()
            self.assertEqual(self.sync_record.email, 'test@example.com')
            self.assertTrue(self.sync_record.active)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_list(self, mock_request):
        """Test retrieving lists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{'name': 'List 1', 'id': 'lc1'}]
        }
        mock_request.return_value = mock_response
        
        self.sync_record.get_list(self.sync_record.id)
        lists = self.env['mailer.cloud.list'].search([('authorization_id', '=', self.sync_record.id)])
        self.assertEqual(len(lists), 1)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_properties(self, mock_request):
        """Test retrieving properties."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{'field_value': 'New Prop', 'field_type': 'Text', 'id': 'p1'}]
        }
        mock_request.return_value = mock_response
        
        self.sync_record.get_properties()
        prop = self.env['mailer.cloud.properties'].search([('name', '=', 'New Prop')])
        self.assertTrue(prop)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_contact_sync(self, mock_request):
        """Test batch contact sync."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Batch List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.list_id = test_list.id
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        self.sync_record.action_contact_sync()
        self.assertTrue(mock_request.called)
