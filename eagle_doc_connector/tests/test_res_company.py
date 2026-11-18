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
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import EagleDocCommon


@tagged('post_install', '-at_install')
class TestResCompany(EagleDocCommon):
    """Tests for res company."""

    def setUp(self):
        """Prepare the fixtures for each test."""
        super().setUp()
        self.company.eagle_sub_business_id = False

    def test_write_flags_profile_out_of_sync(self):
        """Write flags profile out of sync."""
        self.company.eagle_sub_business_id = 'SB1'
        self.company.is_eagle_doc_profile_synced = True
        self.company.write({'street': 'New street 1'})
        self.assertFalse(self.company.is_eagle_doc_profile_synced)

    def test_write_without_link_keeps_flag(self):
        """Write without link keeps flag."""
        self.company.is_eagle_doc_profile_synced = True
        self.company.write({'street': 'New street 1'})
        self.assertTrue(self.company.is_eagle_doc_profile_synced)

    def test_create_sub_business(self):
        """Create sub business."""
        with self.patch_http('post', self._resp({'id': 'SB9'})):
            action = self.company.action_eagle_create_sub_business()
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(self.company.eagle_sub_business_id, 'SB9')
        self.assertTrue(self.company.is_eagle_doc_profile_synced)

    def test_create_sub_business_errors(self):
        """Create sub business errors."""
        with self.patch_http('post', self._resp({})):
            with self.assertRaises(UserError):
                self.company.action_eagle_create_sub_business()
        self.company.eagle_sub_business_id = 'SB1'
        with self.assertRaises(UserError):
            self.company.action_eagle_create_sub_business()

    def test_refresh_sub_business(self):
        """Refresh sub business."""
        with self.assertRaises(UserError):
            self.company.action_eagle_refresh_sub_business()
        self.company.eagle_sub_business_id = 'SB1'
        with self.patch_http('get', self._resp({'id': 'SB1'})):
            action = self.company.action_eagle_refresh_sub_business()
        self.assertEqual(action['tag'], 'display_notification')
        self.assertIn('SB1', action['params']['message'])

    def test_update_sub_business(self):
        """Update sub business."""
        with self.assertRaises(UserError):
            self.company.action_eagle_update_sub_business()
        self.company.eagle_sub_business_id = 'SB1'
        self.company.is_eagle_doc_profile_synced = False
        with self.patch_http('patch', self._resp({'id': 'SB1'})):
            action = self.company.action_eagle_update_sub_business()
        self.assertEqual(action['tag'], 'display_notification')
        self.assertTrue(self.company.is_eagle_doc_profile_synced)

    def test_delete_sub_business(self):
        """Delete sub business."""
        with self.assertRaises(UserError):
            self.company.action_eagle_delete_sub_business()
        self.company.eagle_sub_business_id = 'SB1'
        with self.patch_http('delete', self._resp({}, 204)):
            action = self.company.action_eagle_delete_sub_business()
        self.assertEqual(action['tag'], 'display_notification')
        self.assertFalse(self.company.eagle_sub_business_id)

    def test_batch_create(self):
        """Batch create."""
        other = self.env['res.company'].create({'name': 'Second Co'})
        failing = self.env['res.company'].create({'name': 'Failing Co'})
        existing = self.env['res.company'].create({
            'name': 'Linked Co', 'eagle_sub_business_id': 'OLD'})
        companies = self.company | other | failing | existing
        payload = {'results': [
            {'externalRef': f'odoo-company-{self.company.id}',
             'outcome': 'CREATED', 'subBusinessId': 'A'},
            {'externalRef': f'odoo-company-{other.id}',
             'outcome': 'EXISTS', 'subBusinessId': 'B'},
            {'externalRef': f'odoo-company-{failing.id}',
             'outcome': 'FAILED', 'error': 'nope'},
            {'externalRef': 'odoo-company-unknown', 'outcome': 'CREATED',
             'subBusinessId': 'Z'},
        ]}
        with self.patch_http('post', self._resp(payload)):
            action = companies.action_eagle_batch_create_sub_businesses()
        self.assertEqual(self.company.eagle_sub_business_id, 'A')
        self.assertEqual(other.eagle_sub_business_id, 'B')
        self.assertFalse(failing.eagle_sub_business_id)
        self.assertEqual(action['params']['type'], 'warning')
        self.assertTrue(action['params']['sticky'])

    def test_batch_create_all_success(self):
        """Batch create all success."""
        payload = {'results': [{
            'externalRef': f'odoo-company-{self.company.id}',
            'outcome': 'CREATED', 'subBusinessId': 'A'}]}
        with self.patch_http('post', self._resp(payload)):
            action = self.company.action_eagle_batch_create_sub_businesses()
        self.assertEqual(action['params']['type'], 'success')

    def test_batch_create_nothing_to_do(self):
        """Batch create nothing to do."""
        self.company.eagle_sub_business_id = 'SB1'
        with self.assertRaises(UserError):
            self.company.action_eagle_batch_create_sub_businesses()

    @staticmethod
    def _resp(payload, status=200):
        from .common import FakeResponse
        return FakeResponse(status, payload)
