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
class TestResPartner(TransactionCase):
    """Tests for res.partner Pipedrive overrides."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.api_key = 'test-api-key'
        cls.company.contact_synced = False
        cls.PipedriveRecord = cls.env['pipedrive.record']

    def test_01_pipedrive_reference_field(self):
        """pipedrive_reference field exists on res.partner."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({
                'name': 'Ref Partner', 'pipedrive_reference': 'PD-P-1',
            })
        self.assertEqual(partner.pipedrive_reference, 'PD-P-1')

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_partner.requests.put')
    def test_02_write_synced_partner_calls_api(self, mock_put):
        """Writing to a synced partner sends PUT to Pipedrive."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({
                'name': 'Synced Partner',
            })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-p-10',
            'record_type': 'partner',
            'odoo_ref': partner.id,
        })
        mock_put.return_value = _mock_response({'success': True, 'data': {}})
        partner.with_context(skip_pipedrive_sync=False).write({'name': 'Updated Partner'})
        mock_put.assert_called_once()

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_partner.requests.put')
    def test_03_write_unsynced_partner_no_api(self, mock_put):
        """Writing to an un-synced partner does NOT call the API."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({
                'name': 'Local Partner',
            })
        partner.write({'name': 'Still Local'})
        mock_put.assert_not_called()

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_partner.requests.put')
    def test_04_write_with_skip_context(self, mock_put):
        """Writing with skip_pipedrive_sync context skips the API call."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({'name': 'Skip Partner'})
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-skip',
            'record_type': 'partner',
            'odoo_ref': partner.id,
        })
        partner.with_context(skip_pipedrive_sync=True).write({
            'name': 'Skipped Update',
        })
        mock_put.assert_not_called()

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_partner.requests.put')
    def test_05_write_email_sends_email_payload(self, mock_put):
        """Writing email sends email in Pipedrive format."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({
                'name': 'Email Partner', 'email': 'old@test.com',
            })
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-email',
            'record_type': 'partner',
            'odoo_ref': partner.id,
        })
        mock_put.return_value = _mock_response({'success': True, 'data': {}})
        partner.with_context(skip_pipedrive_sync=False).write({'email': 'new@test.com'})
        mock_put.assert_called_once()

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_partner.requests.delete')
    def test_06_unlink_synced_partner(self, mock_delete):
        """Deleting a synced partner sends DELETE to Pipedrive."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({'name': 'Delete Partner'})
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-p-del',
            'record_type': 'partner',
            'odoo_ref': partner.id,
        })
        mock_delete.return_value = _mock_response({'success': True})
        partner.with_context(skip_pipedrive_sync=False).unlink()
        mock_delete.assert_called_once()

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_partner.requests.delete')
    def test_07_unlink_unsynced_partner(self, mock_delete):
        """Deleting an un-synced partner does NOT call the API."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({'name': 'Local Delete'})
        partner.with_context(skip_pipedrive_sync=True).unlink()
        mock_delete.assert_not_called()

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_partner.requests.post')
    def test_08_create_partner_with_sync(self, mock_post):
        """Creating a partner with contact_synced=True exports to Pipedrive."""
        self.company.contact_synced = True
        mock_post.return_value = _mock_response({
            'success': True, 'data': {'id': 'new-p-1'},
        })
        partner = self.env['res.partner'].create({
            'name': 'Auto Export Partner',
            'email': 'auto@test.com',
        })
        self.assertTrue(partner.exists())
        mock_post.assert_called_once()

    def test_09_create_partner_without_sync(self):
        """Creating a partner with contact_synced=False does no export."""
        self.company.contact_synced = False
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({'name': 'No Export Partner'})
        self.assertTrue(partner.exists())

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_partner.requests.delete')
    def test_10_unlink_with_skip_context(self, mock_delete):
        """Unlink with skip_pipedrive_sync context skips the API call."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({'name': 'Skip Delete'})
        self.PipedriveRecord.create({
            'pipedrive_reference': 'pd-skip-del',
            'record_type': 'partner',
            'odoo_ref': partner.id,
        })
        partner.with_context(skip_pipedrive_sync=True).unlink()
        mock_delete.assert_not_called()
