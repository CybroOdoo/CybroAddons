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
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase


class TestMailerCloudProperties(TransactionCase):

    def setUp(self):
        super(TestMailerCloudProperties, self).setUp()
        self.sync_record = self.env['mailer.cloud.api.sync'].create({
            'api_key': 'test_api_key',
            'name': 'Test Sync',
            'active': True
        })

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_properties.requests.request')
    def test_property_sync_on_create(self, mock_request):
        """Test that creating a property triggers a sync call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'remote_p1'}
        mock_request.return_value = mock_response

        prop = self.env['mailer.cloud.properties'].create({
            'name': 'Test New Property',
            'type': 'text',
            'authorization_id': self.sync_record.id
        })

        self.assertTrue(mock_request.called)
        self.assertEqual(prop.mailer_cloud, 'remote_p1')

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_properties.requests.request')
    def test_property_create_with_existing_mailer_cloud(self, mock_request):
        """Test that creating a property with already set mailer_cloud skips API call."""
        prop = self.env['mailer.cloud.properties'].create({
            'name': 'Existing Property',
            'type': 'text',
            'mailer_cloud': 'existing_id',
            'authorization_id': self.sync_record.id
        })
        self.assertFalse(mock_request.called)
        self.assertEqual(prop.mailer_cloud, 'existing_id')

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_properties.requests.request')
    def test_property_create_without_authorization(self, mock_request):
        """Test that creating a property without authorization_id skips API call."""
        prop = self.env['mailer.cloud.properties'].create({
            'name': 'No Auth Property',
            'type': 'text',
        })
        self.assertFalse(mock_request.called)
        self.assertFalse(prop.mailer_cloud)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_properties.requests.request')
    def test_property_create_api_failure(self, mock_request):
        """Test that API failure during property creation is handled gracefully."""
        mock_request.side_effect = Exception("Connection timed out")
        prop = self.env['mailer.cloud.properties'].create({
            'name': 'Fail Property',
            'type': 'text',
            'authorization_id': self.sync_record.id
        })
        self.assertTrue(mock_request.called)
        self.assertFalse(prop.mailer_cloud)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_properties.requests.request')
    def test_property_create_no_id_in_response(self, mock_request):
        """Test that property create handles status 200 without 'id' in response gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'ok'}
        mock_request.return_value = mock_response

        prop = self.env['mailer.cloud.properties'].create({
            'name': 'No Id Property',
            'type': 'number',
            'authorization_id': self.sync_record.id
        })
        self.assertTrue(mock_request.called)
        self.assertFalse(prop.mailer_cloud)

    @patch('odoo.addons.mailer_cloud_connector.models.mailer_cloud_properties.requests.request')
    def test_property_create_multi(self, mock_request):
        """Test creating multiple properties at once."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'batch_p_id'}
        mock_request.return_value = mock_response

        props = self.env['mailer.cloud.properties'].create([
            {'name': 'Multi Prop 1', 'type': 'text', 'authorization_id': self.sync_record.id},
            {'name': 'Multi Prop 2', 'type': 'date', 'authorization_id': self.sync_record.id},
            {
                'name': 'Multi Prop Existing',
                'type': 'number',
                'mailer_cloud': 'preset_id',
                'authorization_id': self.sync_record.id,
            },
        ])
        self.assertEqual(len(props), 3)
        # Should call API for the 2 properties without mailer_cloud
        self.assertEqual(mock_request.call_count, 2)
        self.assertEqual(props[0].mailer_cloud, 'batch_p_id')
        self.assertEqual(props[1].mailer_cloud, 'batch_p_id')
        self.assertEqual(props[2].mailer_cloud, 'preset_id')
