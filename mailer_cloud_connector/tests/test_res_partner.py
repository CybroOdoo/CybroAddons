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

    def test_compute_partner_type(self):
        """Test the partner type computation."""
        partner = self.PartnerModel.create({'name': 'Test Partner'})
        # Using patch to set computed/read-only fields for logic testing
        with patch.object(type(partner), 'sale_order_count', new=1), \
             patch.object(type(partner), 'purchase_order_count', new=0):
            partner._compute_partner_type()
            self.assertEqual(partner.partner_type, 'Customer')

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
        
        # Mapping name field
        prop = self.env.ref('mailer_cloud_connector.property_data_name')
        prop.mailer_cloud = 'remote_name_id'  # Critical: Needs a remote ID to trigger sync logic
        
        self.env['contact.sync'].create({
            'property_id': prop.id,
            'contact_fields': 'name',
            'sync_id': self.sync_record.id
        })
        
        self.env.flush_all() # Ensure records are in DB for the search in partner create

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        self.PartnerModel.create({'name': 'Sync Partner', 'email': 'sync@example.com'})
        self.assertTrue(mock_request.called, "API request was not called on partner creation")
