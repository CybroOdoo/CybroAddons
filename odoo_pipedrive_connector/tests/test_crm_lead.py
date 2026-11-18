# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
from unittest.mock import patch
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from .common import mock_response, route_responses


@tagged('post_install', '-at_install')
class TestCrmLead(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'api_key': 'test_api_key',
            'contact_synced': False,
            'lead_synced': True,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Synced Customer',
            'pipedrive_reference': '8001',
        })
        cls.new_partner = cls.env['res.partner'].create(
            {'name': 'Unsynced Customer'})

    def _create_synced_lead(self):
        """Create a lead that already exists in Pipedrive"""
        lead = self.env['crm.lead'].create({'name': 'Synced Lead'})
        lead.pipedrive_reference = 'lead-uuid-10'
        self.env['pipedrive.record'].create({
            'pipedrive_reference': 'lead-uuid-10',
            'record_type': 'lead',
            'odoo_ref': lead.id,
        })
        return lead

    @patch('requests.post')
    def test_create_lead(self, mock_post):
        """A new lead with a customer is created in Pipedrive."""
        mock_post.return_value = mock_response(
            {'success': True, 'data': {'id': 'lead-uuid-11'}})
        lead = self.env['crm.lead'].create({
            'name': 'New Lead',
            'partner_id': self.partner.id,
            'expected_revenue': 250.0,
        })
        self.assertEqual(lead.pipedrive_reference, 'lead-uuid-11')
        self.assertEqual(mock_post.call_args.kwargs['json']['person_id'], 8001)
        self.assertTrue(self.env['pipedrive.record'].search(
            [('record_type', '=', 'lead'), ('odoo_ref', '=', lead.id)]))

    @patch('requests.post')
    def test_create_lead_new_customer(self, mock_post):
        """A customer missing in Pipedrive is created before the lead."""
        mock_post.side_effect = route_responses({
            'persons': {'success': True, 'data': {'id': 8002}},
            'leads': {'success': True, 'data': {'id': 'lead-uuid-12'}},
        })
        lead = self.env['crm.lead'].create({
            'name': 'Lead For New Customer',
            'partner_id': self.new_partner.id,
        })
        self.assertEqual(self.new_partner.pipedrive_reference, '8002')
        self.assertEqual(lead.pipedrive_reference, 'lead-uuid-12')

    @patch('requests.post')
    def test_create_lead_without_customer(self, mock_post):
        """Leads without a customer are not sent to Pipedrive."""
        lead = self.env['crm.lead'].create({'name': 'Lead Without Customer'})
        mock_post.assert_not_called()
        self.assertFalse(lead.pipedrive_reference)

    @patch('requests.post')
    def test_create_lead_error(self, mock_post):
        mock_post.return_value = mock_response(
            {'success': False, 'error': 'Lead not created',
             'error_info': 'Invalid person'})
        with self.assertRaises(ValidationError):
            self.env['crm.lead'].create({
                'name': 'Failing Lead',
                'partner_id': self.partner.id,
            })

    @patch('requests.patch')
    def test_write_lead(self, mock_patch):
        """Name, customer and revenue changes are sent to Pipedrive."""
        lead = self._create_synced_lead()
        mock_patch.return_value = mock_response({'success': True})
        lead.write({
            'name': 'Renamed Lead',
            'partner_id': self.partner.id,
            'expected_revenue': 900.0,
        })
        self.assertEqual(lead.name, 'Renamed Lead')
        mock_patch.assert_called_once()

    @patch('requests.post')
    @patch('requests.patch')
    def test_write_lead_new_customer(self, mock_patch, mock_post):
        lead = self._create_synced_lead()
        mock_post.return_value = mock_response(
            {'success': True, 'data': {'id': 8003}})
        mock_patch.return_value = mock_response({'success': True})
        lead.write({'partner_id': self.new_partner.id})
        self.assertEqual(self.new_partner.pipedrive_reference, '8003')

    @patch('requests.patch')
    def test_write_lead_error(self, mock_patch):
        lead = self._create_synced_lead()
        mock_patch.return_value = mock_response({'error': 'Lead not found'})
        with self.assertRaises(ValidationError):
            lead.write({'name': 'Renamed Lead'})

    @patch('requests.delete')
    def test_unlink_lead(self, mock_delete):
        lead = self._create_synced_lead()
        mock_delete.return_value = mock_response({'success': True})
        lead.unlink()
        self.assertFalse(lead.exists())
        mock_delete.assert_called_once()

    @patch('requests.delete')
    def test_unlink_lead_error(self, mock_delete):
        lead = self._create_synced_lead()
        mock_delete.return_value = mock_response({'error': 'Lead not found'})
        with self.assertRaises(ValidationError):
            lead.unlink()
