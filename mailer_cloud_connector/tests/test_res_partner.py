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
from odoo import fields


class TestResPartner(TransactionCase):

    def setUp(self):
        super(TestResPartner, self).setUp()
        self.PartnerModel = self.env['res.partner']
        self.SyncModel = self.env['mailer.cloud.api.sync']

        self.sync_record = self.SyncModel.create({
            'api_key': 'test_api_key',
            'name': 'Test Sync',
            'contact_sync_active': False,
            'active': True
        })

    def test_compute_partner_type_default(self):
        """Test default partner type computation when counts are zero."""
        partner = self.PartnerModel.create({'name': 'Test Partner'})
        partner._compute_partner_type()
        self.assertFalse(partner.partner_type)

    def test_compute_partner_type_customer(self):
        """Test partner type computation for customer."""
        partner = self.PartnerModel.create({'name': 'Customer Partner'})
        target = getattr(type(partner), '_fields__', None)
        patcher = (
            patch.dict(target, {'sale_order_count': fields.Integer()})
            if isinstance(target, dict)
            else patch.object(type(partner), '_fields', dict(type(partner)._fields, sale_order_count=fields.Integer()))
        )
        with patcher, patch.object(type(partner), 'sale_order_count', 5, create=True):
            partner._compute_partner_type()
            self.assertEqual(partner.partner_type, "Customer")

    def test_compute_partner_type_vendor(self):
        """Test partner type computation for vendor."""
        partner = self.PartnerModel.create({'name': 'Vendor Partner'})
        target = getattr(type(partner), '_fields__', None)
        patcher = (
            patch.dict(target, {'purchase_order_count': fields.Integer()})
            if isinstance(target, dict)
            else patch.object(type(partner), '_fields', dict(type(partner)._fields, purchase_order_count=fields.Integer()))
        )
        with patcher, patch.object(type(partner), 'purchase_order_count', 3, create=True):
            partner._compute_partner_type()
            self.assertEqual(partner.partner_type, "Vendor")

    def test_compute_partner_type_vendor_and_customer(self):
        """Test partner type computation for vendor and customer."""
        partner = self.PartnerModel.create({'name': 'Vendor and Customer Partner'})
        extra_fields = {
            'sale_order_count': fields.Integer(),
            'purchase_order_count': fields.Integer(),
        }
        target = getattr(type(partner), '_fields__', None)
        patcher = (
            patch.dict(target, extra_fields)
            if isinstance(target, dict)
            else patch.object(type(partner), '_fields', dict(type(partner)._fields, **extra_fields))
        )
        with patcher, \
             patch.object(type(partner), 'sale_order_count', 2, create=True), \
             patch.object(type(partner), 'purchase_order_count', 4, create=True):
            partner._compute_partner_type()
            self.assertEqual(partner.partner_type, "Vendor and Customer")

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_create(self, mock_request):
        """Test partner creation triggers sync when active."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        prop = self.env.ref('mailer_cloud_connector.property_data_name')
        prop.mailer_cloud = 'remote_name_id'

        self.env['contact.sync'].create({
            'property_id': prop.id,
            'contact_fields': 'name',
            'sync_id': self.sync_record.id
        })

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        partner = self.PartnerModel.create({'name': 'Sync Partner', 'email': 'sync@example.com'})
        self.assertTrue(partner)
        self.assertTrue(mock_request.called, "API request was not called on partner creation")
        _, kwargs = mock_request.call_args
        payload = json.loads(kwargs['data'])
        self.assertEqual(payload.get('email'), 'sync@example.com')
        self.assertEqual(payload.get('list_id'), 'l1')
        self.assertEqual(payload.get('custom_fields', {}).get('remote_name_id'), 'Sync Partner')

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_create_multi(self, mock_request):
        """Test creating multiple partners at once (@api.model_create_multi)."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Multi List', 'mailer_cloud': 'l_multi', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # 2 partners with email, 1 without email
        partners = self.PartnerModel.create([
            {'name': 'Multi Partner 1', 'email': 'mp1@example.com'},
            {'name': 'Multi Partner 2', 'email': 'mp2@example.com'},
            {'name': 'Multi Partner No Email'},
        ])
        self.assertEqual(len(partners), 3)
        # Should call API only for the 2 partners with email
        self.assertEqual(mock_request.call_count, 2)

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_create_inactive(self, mock_request):
        """Test partner creation does not trigger sync when contact_sync_active is False."""
        self.sync_record.write({'contact_sync_active': False})
        partner = self.PartnerModel.create({'name': 'Inactive Sync Partner', 'email': 'inactive@example.com'})
        self.assertTrue(partner)
        self.assertFalse(mock_request.called)

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_create_error(self, mock_request):
        """Test partner creation logs error and succeeds when API returns error status."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"errors": [{"message": "Invalid contact data"}]}'
        mock_response.json.return_value = {'errors': [{'message': 'Invalid contact data'}]}
        mock_request.return_value = mock_response

        # Does not raise ValidationError; partner is saved and error is logged
        partner = self.PartnerModel.create({'name': 'Error Partner', 'email': 'err@example.com'})
        self.assertTrue(partner)
        self.assertTrue(mock_request.called)

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_create_general_exception(self, mock_request):
        """Test partner creation logs exception and succeeds on connection error."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        mock_request.side_effect = Exception("Mailercloud API unreachable")

        partner = self.PartnerModel.create({'name': 'Exception Partner', 'email': 'exc@example.com'})
        self.assertTrue(partner)
        self.assertTrue(mock_request.called)

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_create_no_email(self, mock_request):
        """Test partner creation without email does not trigger API sync."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        partner = self.PartnerModel.create({'name': 'No Email Partner'})
        self.assertTrue(partner)
        self.assertFalse(mock_request.called)

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_write(self, mock_request):
        """Test partner write triggers API sync when active."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        prop = self.env.ref('mailer_cloud_connector.property_data_name')
        prop.mailer_cloud = 'remote_name_id'
        self.env['contact.sync'].create({
            'property_id': prop.id,
            'contact_fields': 'name',
            'sync_id': self.sync_record.id
        })

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        partner = self.PartnerModel.create({'name': 'Original Name', 'email': 'write_test@example.com'})
        mock_request.reset_mock()

        partner.write({'name': 'Updated Name'})
        self.assertTrue(mock_request.called, "API request was not called on partner update")
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "PUT")
        self.assertIn("write_test@example.com", args[1])
        payload = json.loads(kwargs['data'])
        self.assertEqual(payload['custom_fields']['remote_name_id'], 'Updated Name')

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_write_email_change(self, mock_request):
        """Test partner write with email change PUTs to old email endpoint with new email in body."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        prop_name = self.env.ref('mailer_cloud_connector.property_data_name')
        prop_name.mailer_cloud = 'remote_name_id'
        self.env['contact.sync'].create({
            'property_id': prop_name.id,
            'contact_fields': 'name',
            'sync_id': self.sync_record.id
        })

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        partner = self.PartnerModel.create({'name': 'Original Name', 'email': 'old_email@example.com'})
        mock_request.reset_mock()

        partner.write({'email': 'new_email@example.com'})
        self.assertTrue(mock_request.called)
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "PUT")
        # Ensure PUT target is old_email@example.com
        self.assertIn("old_email@example.com", args[1])
        payload = json.loads(kwargs['data'])
        self.assertEqual(payload['email'], 'new_email@example.com')

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_write_new_email_added(self, mock_request):
        """Test partner write when email is added to a partner who had no email previously."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        prop = self.env.ref('mailer_cloud_connector.property_data_name')
        prop.mailer_cloud = 'remote_name_id'
        self.env['contact.sync'].create({
            'property_id': prop.id,
            'contact_fields': 'name',
            'sync_id': self.sync_record.id
        })

        partner = self.PartnerModel.create({'name': 'Previously No Email'})
        mock_request.reset_mock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Adding email now -> should POST to /contacts since contact is newly synced
        partner.write({'email': 'newly_added@example.com'})
        self.assertTrue(mock_request.called)
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "POST")
        payload = json.loads(kwargs['data'])
        self.assertEqual(payload['email'], 'newly_added@example.com')

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_write_unmapped_field(self, mock_request):
        """Test partner write when updated field is not in mappings skips API call."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        prop = self.env.ref('mailer_cloud_connector.property_data_name')
        self.env['contact.sync'].create({
            'property_id': prop.id,
            'contact_fields': 'name',
            'sync_id': self.sync_record.id
        })

        partner = self.PartnerModel.create({'name': 'Test Partner', 'email': 'test@example.com'})
        mock_request.reset_mock()

        # Update an unmapped field, e.g., comment
        partner.write({'comment': 'Some notes'})
        self.assertFalse(mock_request.called)

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_write_no_email(self, mock_request):
        """Test partner write without email skips API sync."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        partner = self.PartnerModel.create({'name': 'No Email Partner'})
        mock_request.reset_mock()

        partner.write({'name': 'Changed Name'})
        self.assertFalse(mock_request.called)

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_write_inactive(self, mock_request):
        """Test partner write does not trigger sync when contact_sync_active is False."""
        self.sync_record.write({'contact_sync_active': False})
        partner = self.PartnerModel.create({'name': 'Test Partner', 'email': 'test@example.com'})
        mock_request.reset_mock()

        partner.write({'name': 'Updated Name'})
        self.assertFalse(mock_request.called)

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_write_error(self, mock_request):
        """Test partner write logs error and does not raise ValidationError on API exception."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        prop = self.env.ref('mailer_cloud_connector.property_data_name')
        prop.mailer_cloud = 'remote_name_id'
        self.env['contact.sync'].create({
            'property_id': prop.id,
            'contact_fields': 'name',
            'sync_id': self.sync_record.id
        })

        partner = self.PartnerModel.create({'name': 'Original Name', 'email': 'write_err@example.com'})
        mock_request.side_effect = Exception("Network Connection Error")

        # Does not raise ValidationError; partner is updated and error is logged
        partner.write({'name': 'New Name'})
        self.assertEqual(partner.name, 'New Name')

    @patch('odoo.addons.mailer_cloud_connector.models.res_partner.requests.request')
    def test_partner_sync_on_write_status_error(self, mock_request):
        """Test partner write logs warning when API returns >= 400 status."""
        test_list = self.env['mailer.cloud.list'].create({
            'name': 'Test List', 'mailer_cloud': 'l1', 'authorization_id': self.sync_record.id
        })
        self.sync_record.write({
            'contact_sync_active': True,
            'list_id': test_list.id,
            'contact_sync_time': fields.Datetime.now()
        })
        prop = self.env.ref('mailer_cloud_connector.property_data_name')
        prop.mailer_cloud = 'remote_name_id'
        self.env['contact.sync'].create({
            'property_id': prop.id,
            'contact_fields': 'name',
            'sync_id': self.sync_record.id
        })

        partner = self.PartnerModel.create({'name': 'Original Name', 'email': 'write_err400@example.com'})
        mock_request.reset_mock()

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"errors": [{"message": "Contact not found"}]}'
        mock_request.return_value = mock_response

        # Does not raise ValidationError
        partner.write({'name': 'New Name 400'})
        self.assertEqual(partner.name, 'New Name 400')
        self.assertTrue(mock_request.called)
