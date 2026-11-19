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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import json
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


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

        with patch.object(type(self.SyncModel), 'get_list') as mock_list, \
             patch.object(type(self.SyncModel), 'get_properties') as mock_props:
            self.sync_record.action_sync()
            self.assertEqual(self.sync_record.email, 'test@example.com')
            self.assertEqual(self.sync_record.name, 'Test User')
            self.assertEqual(self.sync_record.plan, 'Free')
            self.assertEqual(self.sync_record.remaining_contacts, 100)
            self.assertEqual(self.sync_record.total_contacts, 1000)
            self.assertEqual(self.sync_record.used_contacts, 900)
            self.assertTrue(self.sync_record.active)
            self.assertTrue(mock_list.called)
            self.assertTrue(mock_props.called)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_sync_error(self, mock_request):
        """Test action_sync raises ValidationError when plan API fails."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'errors': [{'message': 'Invalid API Key'}]}
        mock_request.return_value = mock_response

        with patch.object(type(self.SyncModel), 'get_properties'):
            with self.assertRaises(ValidationError):
                self.sync_record.action_sync()

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_sync_general_exception(self, mock_request):
        """Test action_sync raises ValidationError on network or unexpected exception."""
        mock_request.side_effect = Exception("Network Connection Refused")
        with patch.object(type(self.SyncModel), 'get_properties'):
            with self.assertRaises(ValidationError):
                self.sync_record.action_sync()

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_list(self, mock_request):
        """Test retrieving lists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{'name': 'List 1', 'id': 'lc1'}, {'name': 'List 2', 'id': 'lc2'}]
        }
        mock_request.return_value = mock_response

        self.sync_record.get_list(self.sync_record.id)
        lists = self.env['mailer.cloud.list'].search([('authorization_id', '=', self.sync_record.id)])
        self.assertEqual(len(lists), 2)
        self.assertIn('List 1', lists.mapped('name'))
        self.assertIn('List 2', lists.mapped('name'))

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_list_error_400(self, mock_request):
        """Test get_list raises ValidationError on 400 Bad Request."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': {'message': 'Bad Request'}}
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.sync_record.get_list(self.sync_record.id)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_list_error_401(self, mock_request):
        """Test get_list raises ValidationError on 401 Unauthorized."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'errors': [{'message': 'Unauthorized'}]}
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.sync_record.get_list(self.sync_record.id)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_list_general_exception(self, mock_request):
        """Test get_list raises ValidationError on general exception."""
        mock_request.side_effect = Exception("Connection Timeout")
        with self.assertRaises(ValidationError):
            self.sync_record.get_list(self.sync_record.id)

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
        self.assertEqual(prop.type, 'text')
        self.assertEqual(prop.mailer_cloud, 'p1')

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_properties_different_types(self, mock_request):
        """Test property type mappings for Number, Date, and Textarea."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'field_value': 'Num Prop', 'field_type': 'Number', 'id': 'p_num'},
                {'field_value': 'Date Prop', 'field_type': 'Date', 'id': 'p_date'},
                {'field_value': 'Area Prop', 'field_type': 'Textarea', 'id': 'p_area'},
            ]
        }
        mock_request.return_value = mock_response

        self.sync_record.get_properties()
        num_prop = self.env['mailer.cloud.properties'].search([('name', '=', 'Num Prop')])
        date_prop = self.env['mailer.cloud.properties'].search([('name', '=', 'Date Prop')])
        area_prop = self.env['mailer.cloud.properties'].search([('name', '=', 'Area Prop')])

        self.assertEqual(len(num_prop), 1)
        self.assertEqual(num_prop.type, 'number')
        self.assertEqual(date_prop.type, 'date')
        self.assertEqual(area_prop.type, 'textarea')

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_properties_skips_existing(self, mock_request):
        """Test that get_properties skips properties already existing in the database."""
        self.env['mailer.cloud.properties'].create({
            'name': 'Already In DB',
            'type': 'text',
            'authorization_id': self.sync_record.id,
        })
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'field_value': 'Already In DB', 'field_type': 'Text', 'id': 'p_dup'},
            ]
        }
        mock_request.return_value = mock_response

        self.sync_record.get_properties()
        existing = self.env['mailer.cloud.properties'].search([('name', '=', 'Already In DB')])
        self.assertEqual(len(existing), 1)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_properties_error_400(self, mock_request):
        """Test get_properties raises ValidationError on 400 Bad Request."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': {'message': 'Bad Request'}}
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.sync_record.get_properties()

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_properties_error_401(self, mock_request):
        """Test get_properties raises ValidationError on 401 Unauthorized."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'errors': [{'message': 'Unauthorized'}]}
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.sync_record.get_properties()

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_get_properties_general_exception(self, mock_request):
        """Test get_properties raises ValidationError on general exception."""
        mock_request.side_effect = Exception("Property Fetch Error")
        with self.assertRaises(ValidationError):
            self.sync_record.get_properties()

    def test_action_contact_sync_no_list(self):
        """Test action_contact_sync raises ValidationError when list_id is not set."""
        self.sync_record.list_id = False
        with self.assertRaises(ValidationError):
            self.sync_record.action_contact_sync()

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_contact_sync_empty_partners(self, mock_request):
        """Test batch contact sync when no partners are present."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Batch List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.list_id = test_list.id

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        self.sync_record.action_contact_sync()
        self.assertTrue(mock_request.called)
        self.assertTrue(self.sync_record.contact_sync_active)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_contact_sync_with_partners(self, mock_request):
        """Test batch contact sync with partners exporting all contacts with email."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Batch List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.list_id = test_list.id
        self.env['res.partner'].create({
            'name': 'Batch Contact 1',
            'email': 'batch1@example.com'
        })
        self.env['res.partner'].create({
            'name': 'Batch Contact 2',
            'email': 'batch2@example.com'
        })
        # Partner without email must be excluded
        self.env['res.partner'].create({
            'name': 'No Email Partner'
        })

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        self.sync_record.action_contact_sync()
        self.assertTrue(mock_request.called)
        self.assertTrue(self.sync_record.contact_sync_active)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_contact_sync_with_mappings_and_types(self, mock_request):
        """Test contact sync correctly formats standard, custom fields, and handles floats."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Custom Batch List', 'mailer_cloud': 'l_custom', 'authorization_id': self.sync_record.id
        })
        self.sync_record.list_id = test_list.id

        # Standard property mapping
        std_prop = self.env.ref('mailer_cloud_connector.property_data_name')
        std_prop.mailer_cloud = False
        self.env['contact.sync'].create({
            'property_id': std_prop.id,
            'contact_fields': 'name',
            'sync_id': self.sync_record.id
        })

        # Custom property mapping
        custom_prop = self.env['mailer.cloud.properties'].create({
            'name': 'Latitude Custom',
            'type': 'number',
            'mailer_cloud': 'custom_remote_prop_id',
            'authorization_id': self.sync_record.id
        })
        self.env['contact.sync'].create({
            'property_id': custom_prop.id,
            'contact_fields': 'partner_latitude',
            'sync_id': self.sync_record.id
        })

        partner = self.env['res.partner'].create({
            'name': 'Mapped Partner',
            'email': 'mapped@example.com',
            'partner_latitude': 1500.75
        })

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        self.sync_record.action_contact_sync()
        self.assertTrue(mock_request.called)
        _, kwargs = mock_request.call_args
        payload = json.loads(kwargs['data'])
        self.assertEqual(payload['list_id'], 'l_custom')
        self.assertEqual(len(payload['contacts']), 1)
        contact_data = payload['contacts'][0]
        self.assertEqual(contact_data['email'], 'mapped@example.com')
        self.assertEqual(contact_data['name'], 'Mapped Partner')
        self.assertEqual(contact_data['custom_fields']['custom_remote_prop_id'], 1501)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_contact_sync_batches_over_100(self, mock_request):
        """Test that more than 100 contacts are dispatched in separate batch requests."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Large List', 'mailer_cloud': 'l_large', 'authorization_id': self.sync_record.id
        })
        self.sync_record.list_id = test_list.id

        # Create 105 partners with emails
        partner_vals = [{'name': f'Partner {i}', 'email': f'p{i}@example.com'} for i in range(105)]
        self.env['res.partner'].create(partner_vals)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        self.sync_record.action_contact_sync()
        # 105 contacts with batch size 100 -> 2 batch requests
        self.assertEqual(mock_request.call_count, 2)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_contact_sync_error_400(self, mock_request):
        """Test action_contact_sync raises ValidationError on 400 error."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Batch List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.list_id = test_list.id

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'errors': {'message': 'Bad Request'}}
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.sync_record.action_contact_sync()

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_contact_sync_error_401(self, mock_request):
        """Test action_contact_sync raises ValidationError on 401 error."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Batch List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.list_id = test_list.id

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'errors': [{'message': 'Unauthorized'}]}
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.sync_record.action_contact_sync()

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_contact_sync_error_status_other(self, mock_request):
        """Test action_contact_sync raises ValidationError on non-200/400/401 status."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Batch List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.list_id = test_list.id

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError):
            self.sync_record.action_contact_sync()

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_sync.requests.request')
    def test_action_contact_sync_general_exception(self, mock_request):
        """Test action_contact_sync raises ValidationError on general exception."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Batch List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.list_id = test_list.id
        mock_request.side_effect = Exception("Batch timeout")

        with self.assertRaises(ValidationError):
            self.sync_record.action_contact_sync()

    def test_mailer_cloud_list_crud(self):
        """Test creating, reading, and unlinking mailer.cloud.list records."""
        ListModel = self.env['mailer.cloud.list']
        new_list = ListModel.create({
            'name': 'Newsletter Subscribers',
            'mailer_cloud': 'remote_list_99',
            'authorization_id': self.sync_record.id
        })
        self.assertEqual(new_list.name, 'Newsletter Subscribers')
        self.assertEqual(new_list.mailer_cloud, 'remote_list_99')
        self.assertEqual(new_list.authorization_id, self.sync_record)

        found = ListModel.search([('authorization_id', '=', self.sync_record.id)])
        self.assertIn(new_list, found)
        new_list.unlink()
        self.assertFalse(ListModel.search([('id', '=', new_list.id)]))
