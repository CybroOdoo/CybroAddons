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
from unittest.mock import patch
from datetime import date
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestEagleDocWizards(TransactionCase):
    """Test suite for Eagle Doc feedback wizard and usage wizard."""

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param('eagle_doc.api_key', 'test_key')
        self.move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'eagle_doc_sub_business_id': 'sub_bus_123',
        })

    def test_01_feedback_wizard_default_get(self):
        """Verify feedback wizard defaults move_id from active_id context."""
        wizard = self.env['eagle.doc.feedback.wizard'].with_context(active_id=self.move.id).create({})
        self.assertEqual(wizard.move_id, self.move)

    @patch('odoo.addons.eagle_doc_connector.models.account_move.AccountMove.action_eagle_doc_submit_vendor_feedback')
    def test_02_feedback_wizard_submit_vendor(self, mock_vendor_fb):
        """Verify submitting vendor correction via wizard."""
        mock_vendor_fb.return_value = {'outcome': 'ACCEPTED'}
        wizard = self.env['eagle.doc.feedback.wizard'].create({
            'move_id': self.move.id,
            'feedback_type': 'vendor',
            'new_vendor_name': 'New Supplier Name',
            'new_vendor_account': 'ACC-999',
        })
        res = wizard.action_submit()

        mock_vendor_fb.assert_called_once_with(
            new_vendor_name='New Supplier Name',
            new_vendor_account='ACC-999',
            new_vendor_city=False,
            new_vendor_street=False,
        )
        self.assertEqual(res.get('type'), 'ir.actions.client')

    @patch('odoo.addons.eagle_doc_connector.models.account_move.AccountMove.action_eagle_doc_submit_product_feedback')
    def test_03_feedback_wizard_submit_product(self, mock_product_fb):
        """Verify submitting product/account correction via wizard."""
        mock_product_fb.return_value = {'outcome': 'ACCEPTED'}
        wizard = self.env['eagle.doc.feedback.wizard'].create({
            'move_id': self.move.id,
            'feedback_type': 'product_account',
            'product_name': 'Sample Product',
            'new_bk_account_number': '4400',
            'new_tax_code': '19',
        })
        res = wizard.action_submit()

        mock_product_fb.assert_called_once()
        self.assertEqual(res.get('type'), 'ir.actions.client')

    def test_04_feedback_wizard_validation_errors(self):
        """Verify UserErrors are raised when required feedback fields are missing."""
        # Unlinked document error
        unlinked_move = self.env['account.move'].create({'move_type': 'in_invoice'})
        wizard_unlinked = self.env['eagle.doc.feedback.wizard'].create({
            'move_id': unlinked_move.id,
            'feedback_type': 'vendor',
            'new_vendor_name': 'Name',
            'new_vendor_account': 'Acc',
        })
        with self.assertRaises(UserError):
            wizard_unlinked.action_submit()

        # Missing vendor details error
        wizard_vendor_missing = self.env['eagle.doc.feedback.wizard'].create({
            'move_id': self.move.id,
            'feedback_type': 'vendor',
            'new_vendor_name': 'Name Only',
        })
        with self.assertRaises(UserError):
            wizard_vendor_missing.action_submit()

    def test_05_usage_wizard_default_get(self):
        """Verify usage wizard period picker defaults to current month/year."""
        today = date.today()
        wizard = self.env['eagle.doc.usage.wizard'].create({})
        self.assertEqual(wizard.period_month, f"{today.month:02d}")
        self.assertEqual(wizard.period_year, str(today.year))

    @patch('odoo.addons.eagle_doc_connector.models.eagle_api.EagleDocAPI.get_usage')
    def test_06_usage_wizard_action_fetch(self, mock_get_usage):
        """Verify usage wizard fetches billing totals and populates wizard lines."""
        mock_get_usage.return_value = {
            'period': '2026-08',
            'totals': {
                'OCR': 25,
                'BOOKKEEPING': 10,
            }
        }
        wizard = self.env['eagle.doc.usage.wizard'].create({
            'period_month': '08',
            'period_year': '2026',
        })
        res = wizard.action_fetch()

        self.assertEqual(wizard.period, '2026-08')
        self.assertEqual(len(wizard.line_ids), 2)
        ocr_line = wizard.line_ids.filtered(lambda l: 'OCR' in l.feature_label)
        self.assertEqual(ocr_line.quantity, 25)
        self.assertEqual(res.get('res_model'), 'eagle.doc.usage.wizard')
