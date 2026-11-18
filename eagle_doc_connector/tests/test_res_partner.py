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
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import EagleDocCommon, FakeResponse


@tagged('post_install', '-at_install')
class TestResPartner(EagleDocCommon):
    """Tests for res partner."""

    def setUp(self):
        """Prepare the fixtures for each test."""
        super().setUp()
        self.company.eagle_sub_business_id = 'SB1'
        self.vendor = self.env['res.partner'].create({
            'name': 'Vendor One', 'supplier_rank': 1, 'vat': 'DE123',
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Customer One', 'customer_rank': 1,
        })
        self.both = self.env['res.partner'].create({
            'name': 'Both', 'customer_rank': 1, 'supplier_rank': 1,
        })
        self.plain = self.env['res.partner'].create({'name': 'Plain'})

    def test_write_flags_unsynced(self):
        """Write flags unsynced."""
        self.vendor.is_eagle_doc_synced = True
        self.vendor.write({'city': 'Berlin'})
        self.assertFalse(self.vendor.is_eagle_doc_synced)

    def test_write_ignores_plain_partner(self):
        """Write ignores plain partner."""
        self.plain.is_eagle_doc_synced = True
        self.plain.write({'city': 'Berlin'})
        self.assertTrue(self.plain.is_eagle_doc_synced)

    def test_payload_types(self):
        """Payload types."""
        self.assertEqual(self.vendor._eagle_doc_vendor_customer_payload()['type'], 'VENDOR')
        self.assertEqual(self.customer._eagle_doc_vendor_customer_payload()['type'], 'CUSTOMER')
        self.assertEqual(self.both._eagle_doc_vendor_customer_payload()['type'], 'BOTH')

    def test_account_number(self):
        """Account number."""
        self.assertEqual(self.vendor._eagle_doc_account_number(), 'DE123')
        self.assertEqual(
            self.customer._eagle_doc_account_number(),
            f'odoo-partner-{self.customer.id}')

    def test_sync_now(self):
        """Sync now."""
        partners = self.vendor | self.customer | self.plain
        result_payload = {
            'created': 1, 'updated': 0, 'failed': 1,
            'results': [{}, {'error': 'bad row'}],
        }
        with self.patch_http('post', FakeResponse(200, result_payload)):
            result = partners.action_eagle_doc_sync_now()
        self.assertEqual(result, {'created': 1, 'updated': 0, 'failed': 1})
        self.assertTrue(self.vendor.is_eagle_doc_synced)
        self.assertFalse(self.customer.is_eagle_doc_synced)

    def test_sync_now_nothing_to_sync(self):
        """Sync now nothing to sync."""
        self.assertFalse(self.plain.action_eagle_doc_sync_now())

    def test_sync_now_requires_accountant(self):
        """Sync now requires accountant."""
        user = self.env['res.users'].create({
            'name': 'Plain user', 'login': 'plain_eagle',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            self.vendor.with_user(user).action_eagle_doc_sync_now()

    def test_cron_syncs_unsynced_partners(self):
        """Cron syncs unsynced partners."""
        payload = {'created': 3, 'updated': 0, 'failed': 0, 'results': []}
        with self.patch_http('post', FakeResponse(200, payload)) as post:
            self.env['res.partner']._cron_sync_eagle_doc_vendor_customers()
            self.assertTrue(post.called)

    def test_cron_survives_api_errors(self):
        """Cron survives api errors."""
        with self.patch_http('post', FakeResponse(500, {'message': 'x'})):
            try:
                self.env['res.partner']._cron_sync_eagle_doc_vendor_customers()
            except UserError:
                self.fail("cron must not propagate API errors")
