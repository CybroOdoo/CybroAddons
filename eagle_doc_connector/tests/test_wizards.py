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

from .common import EagleDocCommon, FakeResponse


@tagged('post_install', '-at_install')
class TestUsageWizard(EagleDocCommon):
    """Tests for usage wizard."""

    def test_default_period(self):
        """Default period."""
        wizard = self.env['eagle.doc.usage.wizard'].create({})
        self.assertTrue(wizard.period_month)
        self.assertTrue(wizard.period_year)

    def test_year_selection(self):
        """Year selection."""
        years = self.env['eagle.doc.usage.wizard']._fields['period_year']
        self.assertEqual(len(years._description_selection(self.env)), 5)

    def test_fetch_builds_lines(self):
        """Fetch builds lines."""
        payload = {'period': '2026-01', 'totals': {'OCR': 7, 'OTHER': 2}}
        wizard = self.env['eagle.doc.usage.wizard'].create({
            'period_month': '01', 'period_year': '2026'})
        with self.patch_http('get', FakeResponse(200, payload)):
            action = wizard.action_fetch()
        self.assertEqual(action['res_id'], wizard.id)
        self.assertEqual(wizard.period, '2026-01')
        labels = wizard.line_ids.mapped('feature_label')
        self.assertIn('OCR (Pages Processed)', labels)
        self.assertIn('OTHER', labels)
        # Fetching again replaces the lines rather than duplicating them.
        with self.patch_http('get', FakeResponse(200, payload)):
            wizard.action_fetch()
        self.assertEqual(len(wizard.line_ids), 2)

    def test_open_usage_wizard(self):
        """Open usage wizard."""
        with self.patch_http('get', FakeResponse(200, {'totals': {}})):
            action = self.env['eagle.doc.usage.wizard']._open_usage_wizard()
        self.assertEqual(action['res_model'], 'eagle.doc.usage.wizard')


@tagged('post_install', '-at_install')
class TestFeedbackWizard(EagleDocCommon):
    """Tests for feedback wizard."""

    def setUp(self):
        """Prepare the fixtures for each test."""
        super().setUp()
        self.move = self.make_move(eagle_doc_sub_business_id='SB1')

    def _wizard(self, **vals):
        vals.setdefault('move_id', self.move.id)
        return self.env['eagle.doc.feedback.wizard'].create(vals)

    def test_default_get_uses_active_id(self):
        """Default get uses active id."""
        wizard = self.env['eagle.doc.feedback.wizard'].with_context(
            active_model='account.move',
            active_id=self.move.id).default_get(['move_id'])
        self.assertEqual(wizard['move_id'], self.move.id)

    def test_default_get_ignores_other_models(self):
        """Default get ignores an active record of another model."""
        wizard = self.env['eagle.doc.feedback.wizard'].with_context(
            active_model='res.partner',
            active_id=self.move.id).default_get(['move_id'])
        self.assertNotIn('move_id', wizard)

    def test_requires_sub_business(self):
        """Requires sub business."""
        self.move.eagle_doc_sub_business_id = False
        with self.assertRaises(UserError):
            self._wizard().action_submit()

    def test_vendor_feedback(self):
        """Vendor feedback."""
        wizard = self._wizard(
            feedback_type='vendor', new_vendor_name='Acme',
            new_vendor_account='70001')
        with self.patch_http('post', FakeResponse(200, {'outcome': 'CREATED'})):
            action = wizard.action_submit()
        self.assertEqual(action['tag'], 'display_notification')

    def test_vendor_feedback_validation(self):
        """Vendor feedback validation."""
        with self.assertRaises(UserError):
            self._wizard(feedback_type='vendor', new_vendor_name='Acme').action_submit()

    def test_product_feedback(self):
        """Product feedback."""
        wizard = self._wizard(
            feedback_type='product_account', new_bk_account_number='4400',
            product_name='Widget', new_tax_code='9')
        with self.patch_http('post', FakeResponse(200, {'outcome': 'UPDATED'})):
            action = wizard.action_submit()
        self.assertEqual(action['tag'], 'display_notification')

    def test_product_feedback_validation(self):
        """Product feedback validation."""
        with self.assertRaises(UserError):
            self._wizard(feedback_type='product_account').action_submit()
