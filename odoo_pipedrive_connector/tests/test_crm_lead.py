# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, tagged


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


@tagged('post_install', '-at_install')
class TestCrmLead(TransactionCase):
    """Tests for crm.lead Pipedrive overrides (write, unlink, create)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.api_key = 'test-api-key'
        cls.company.lead_synced = False
        cls.PipedriveRecord = cls.env['pipedrive.record']
        cls.partner = cls.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({
                'name': 'Lead Test Partner',
                'pipedrive_reference': '1001',
            })

    def test_01_create_lead_without_sync(self):
        """Create a CRM lead when lead_synced=False — no API call."""
        lead = self.env['crm.lead'].create({
            'name': 'No Sync Lead',
            'type': 'opportunity',
        })
        self.assertTrue(lead.exists())
        self.assertEqual(lead.name, 'No Sync Lead')

    @patch('odoo.addons.odoo_pipedrive_connector.models.crm_lead.requests.patch')
    def test_02_write_lead_with_pipedrive_record(self, mock_patch):
        """Updating a synced lead sends PATCH to Pipedrive."""
        lead = self.env['crm.lead'].create({
            'name': 'Synced Lead', 'type': 'opportunity',
        })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'lead-999',
            'record_type': 'lead',
            'odoo_ref': lead.id,
        })
        mock_patch.return_value = _mock_response({'success': True, 'data': {}})
        lead.write({'name': 'Updated Lead'})
        mock_patch.assert_called_once()
        self.assertEqual(lead.name, 'Updated Lead')

    @patch('odoo.addons.odoo_pipedrive_connector.models.crm_lead.requests.patch')
    def test_03_write_lead_without_pipedrive_record(self, mock_patch):
        """Updating an un-synced lead does NOT call the API."""
        lead = self.env['crm.lead'].create({
            'name': 'Local Lead', 'type': 'opportunity',
        })
        lead.write({'name': 'Still Local'})
        mock_patch.assert_not_called()

    @patch('odoo.addons.odoo_pipedrive_connector.models.crm_lead.requests.patch')
    def test_04_write_expected_revenue(self, mock_patch):
        """Writing expected_revenue sends value update to Pipedrive."""
        lead = self.env['crm.lead'].create({
            'name': 'Revenue Lead', 'type': 'opportunity',
        })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'lead-rev',
            'record_type': 'lead',
            'odoo_ref': lead.id,
        })
        mock_patch.return_value = _mock_response({'success': True, 'data': {}})
        lead.write({'expected_revenue': 10000.0})
        mock_patch.assert_called_once()
        call_data = mock_patch.call_args
        self.assertIn('data', call_data.kwargs)

    @patch('odoo.addons.odoo_pipedrive_connector.models.crm_lead.requests.delete')
    def test_05_unlink_lead_with_pipedrive_record(self, mock_delete):
        """Deleting a synced lead sends DELETE to Pipedrive."""
        lead = self.env['crm.lead'].create({
            'name': 'Delete Me Lead', 'type': 'opportunity',
        })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'lead-del',
            'record_type': 'lead',
            'odoo_ref': lead.id,
        })
        mock_delete.return_value = _mock_response({'success': True})
        lead.unlink()
        mock_delete.assert_called_once()

    @patch('odoo.addons.odoo_pipedrive_connector.models.crm_lead.requests.delete')
    def test_06_unlink_lead_without_pipedrive_record(self, mock_delete):
        """Deleting an un-synced lead does NOT call the API."""
        lead = self.env['crm.lead'].create({
            'name': 'Local Delete Lead', 'type': 'opportunity',
        })
        lead.unlink()
        mock_delete.assert_not_called()

    @patch('odoo.addons.odoo_pipedrive_connector.models.crm_lead.requests.post')
    def test_07_create_lead_with_sync_enabled(self, mock_post):
        """Creating a lead with lead_synced=True exports to Pipedrive."""
        self.company.lead_synced = True
        mock_post.return_value = _mock_response({
            'success': True, 'data': {'id': 'new-lead-id'},
        })
        lead = self.env['crm.lead'].create({
            'name': 'Auto Export Lead',
            'type': 'opportunity',
            'partner_id': self.partner.id,
        })
        self.assertTrue(lead.exists())
        mock_post.assert_called_once()

    def test_08_pipedrive_reference_field(self):
        """pipedrive_reference field is writable and readable."""
        lead = self.env['crm.lead'].create({
            'name': 'Ref Lead', 'type': 'opportunity',
            'pipedrive_reference': 'PD-REF-123',
        })
        self.assertEqual(lead.pipedrive_reference, 'PD-REF-123')
