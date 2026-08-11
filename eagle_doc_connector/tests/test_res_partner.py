# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from unittest.mock import patch, MagicMock
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestResPartner(TransactionCase):
    """Test suite for ResPartner vendor/customer sync tracking and payload building."""

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param('eagle_doc.api_key', 'test_key')
        self.env.company.eagle_sub_business_id = 'sub_bus_default'

        self.vendor = self.env['res.partner'].create({
            'name': 'Test Supplier Ltd',
            'vat': 'DE123456789',
            'supplier_rank': 1,
            'street': 'Vendor Str 1',
            'city': 'Berlin',
            'zip': '10115',
            'is_eagle_doc_synced': True,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Test Customer Inc',
            'customer_rank': 1,
            'is_eagle_doc_synced': True,
        })

    def test_01_write_flags_unsynced(self):
        """Verify modifying vendor/customer details clears is_eagle_doc_synced."""
        self.vendor.write({'street': 'Updated Str 2'})
        self.assertFalse(self.vendor.is_eagle_doc_synced)

        self.customer.write({'name': 'Updated Customer Name'})
        self.assertFalse(self.customer.is_eagle_doc_synced)

    def test_02_account_number_generation(self):
        """Verify _eagle_doc_account_number uses VAT or partner ID fallback."""
        self.assertEqual(self.vendor._eagle_doc_account_number(), 'DE123456789')
        self.assertEqual(self.customer._eagle_doc_account_number(), f'odoo-partner-{self.customer.id}')

    def test_03_vendor_customer_payload_building(self):
        """Verify _eagle_doc_vendor_customer_payload output structure and partner types."""
        payload_vendor = self.vendor._eagle_doc_vendor_customer_payload()
        self.assertEqual(payload_vendor['type'], 'VENDOR')
        self.assertEqual(payload_vendor['companyName'], 'Test Supplier Ltd')
        self.assertEqual(payload_vendor['vatId'], 'DE123456789')

        payload_customer = self.customer._eagle_doc_vendor_customer_payload()
        self.assertEqual(payload_customer['type'], 'CUSTOMER')

        both_partner = self.env['res.partner'].create({
            'name': 'Both Partner',
            'supplier_rank': 1,
            'customer_rank': 1,
        })
        self.assertEqual(both_partner._eagle_doc_vendor_customer_payload()['type'], 'BOTH')

    @patch('odoo.addons.eagle_doc_connector.models.res_partner.EagleDocAPI.sync_vendor_customers_batch')
    def test_04_action_eagle_doc_sync_now(self, mock_sync_batch):
        """Verify action_eagle_doc_sync_now executes batch sync and updates flags."""
        def _mock_batch(sub_bus_id, items, timeout=60):
            return {
                'created': len(items),
                'updated': 0,
                'failed': 0,
                'results': [{'outcome': 'CREATED'} for _ in items],
            }
        mock_sync_batch.side_effect = _mock_batch
        self.vendor.is_eagle_doc_synced = False

        res = self.vendor.action_eagle_doc_sync_now()
        self.assertEqual(res['created'], 1)
        self.assertTrue(self.vendor.is_eagle_doc_synced)
        self.assertTrue(self.vendor.eagle_doc_last_sync)

    @patch('odoo.addons.eagle_doc_connector.models.res_partner.EagleDocAPI.sync_vendor_customers_batch')
    def test_05_cron_sync_eagle_doc_vendor_customers(self, mock_sync_batch):
        """Verify cron job picks up unsynced partners."""
        def _mock_batch(sub_bus_id, items, timeout=60):
            return {
                'created': len(items),
                'updated': 0,
                'failed': 0,
                'results': [{'outcome': 'CREATED'} for _ in items],
            }
        mock_sync_batch.side_effect = _mock_batch
        self.vendor.is_eagle_doc_synced = False
        self.customer.is_eagle_doc_synced = False

        self.env['res.partner']._cron_sync_eagle_doc_vendor_customers()
        self.assertTrue(self.vendor.is_eagle_doc_synced)
        self.assertTrue(self.customer.is_eagle_doc_synced)
