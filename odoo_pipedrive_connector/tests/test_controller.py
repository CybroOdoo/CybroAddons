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

import json
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, tagged, HttpCase


@tagged('post_install', '-at_install')
class TestPipedriveWebhookController(HttpCase):
    """Tests for the Pipedrive webhook controller endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.api_key = 'test-api-key'
        cls.PipedriveRecord = cls.env['pipedrive.record']

    def _jsonrpc_post(self, url, payload):
        """Send a JSON-RPC style POST to a webhook endpoint."""
        return self.url_open(
            url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
        )


    # ── Update contact webhook ──────────────────────────────────────────

    def test_03_update_pipedrive_contact(self):
        """Webhook /update_pipedrive_contact updates partner fields."""
        partner = self.env['res.partner'].with_context(
            skip_pipedrive_sync=True).create({
                'name': 'Old Name',
                'email': 'old@test.com',
                'phone': '0000000000',
            })
        partner_id = partner.id
        self.PipedriveRecord.create({
            'pipedrive_reference': 'wh-upd-p1',
            'record_type': 'partner',
            'odoo_ref': partner_id,
        })
        payload = {
            'jsonrpc': '2.0',
            'params': {},
            'current': {
                'id': 'wh-upd-p1',
                'name': 'New Name',
                'email': [{'value': 'new@test.com'}],
                'phone': [{'value': '1111111111'}],
            },
        }
        self._jsonrpc_post('/update_pipedrive_contact', payload)
        # Re-fetch from DB since webhook runs in a separate transaction
        partner_after = self.env['res.partner'].browse(partner_id)
        partner_after.invalidate_recordset()
        self.assertEqual(partner_after.name, 'New Name')
        self.assertEqual(partner_after.email, 'new@test.com')
        self.assertEqual(partner_after.phone, '1111111111')

    # ── Add contact webhook ─────────────────────────────────────────────

    def test_04_add_pipedrive_contact_new(self):
        """Webhook /add_pipedrive_contact creates a new partner."""
        payload = {
            'jsonrpc': '2.0',
            'params': {},
            'meta': {'change_source': 'ui'},
            'current': {
                'id': 'wh-add-p1',
                'name': 'Webhook New Partner',
                'email': [{'value': 'webhook@test.com'}],
                'phone': [{'value': '9999999999'}],
            },
        }
        self._jsonrpc_post('/add_pipedrive_contact', payload)
        rec = self.PipedriveRecord.search([
            ('pipedrive_reference', '=', 'wh-add-p1'),
            ('record_type', '=', 'partner'),
        ])
        self.assertTrue(rec.exists())
        partner = self.env['res.partner'].browse(rec.odoo_ref)
        self.assertEqual(partner.name, 'Webhook New Partner')

    def test_05_add_pipedrive_contact_api_source_ignored(self):
        """Webhook /add_pipedrive_contact with change_source=api is ignored."""
        payload = {
            'jsonrpc': '2.0',
            'params': {},
            'meta': {'change_source': 'api'},
            'current': {
                'id': 'wh-add-p2',
                'name': 'Ignored Partner',
                'email': [{'value': 'ignored@test.com'}],
                'phone': [],
            },
        }
        self._jsonrpc_post('/add_pipedrive_contact', payload)
        rec = self.PipedriveRecord.search([
            ('pipedrive_reference', '=', 'wh-add-p2'),
            ('record_type', '=', 'partner'),
        ])
        self.assertFalse(rec.exists())

    # ── Add product webhook ─────────────────────────────────────────────

    @patch('odoo.addons.odoo_pipedrive_connector.models.res_company.requests.get')
    def test_06_add_pipedrive_product(self, mock_get):
        """Webhook /add_pipedrive_product creates a new product."""
        mock_get.return_value = MagicMock()
        mock_get.return_value.json.return_value = {
            'success': True,
            'data': [{'key': 'category', 'options': []}],
        }
        payload = {
            'jsonrpc': '2.0',
            'params': {},
            'meta': {'change_source': 'ui'},
            'current': {
                'id': 'wh-add-prod-1',
                'name': 'Webhook Product',
                'description': 'A product from webhook',
                'unit': None,
                'category': None,
                'prices': [{'price': 100.0, 'cost': 50.0, 'currency': 'USD'}],
                'tax': 0,
                'active_flag': True,
            },
        }
        self._jsonrpc_post('/add_pipedrive_product', payload)
        rec = self.PipedriveRecord.search([
            ('pipedrive_reference', '=', 'wh-add-prod-1'),
            ('record_type', '=', 'product'),
        ])
        self.assertTrue(rec.exists())

    def test_07_add_pipedrive_product_api_source_ignored(self):
        """Webhook /add_pipedrive_product with change_source=api is ignored."""
        payload = {
            'jsonrpc': '2.0',
            'params': {},
            'meta': {'change_source': 'api'},
            'current': {
                'id': 'wh-add-prod-2',
                'name': 'Ignored Product',
                'description': '',
                'unit': None,
                'category': None,
                'prices': [{'price': 10.0, 'cost': 5.0, 'currency': 'USD'}],
                'tax': 0,
            },
        }
        self._jsonrpc_post('/add_pipedrive_product', payload)
        rec = self.PipedriveRecord.search([
            ('pipedrive_reference', '=', 'wh-add-prod-2'),
            ('record_type', '=', 'product'),
        ])
        self.assertFalse(rec.exists())
