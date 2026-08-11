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
import json
from unittest.mock import patch, MagicMock
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, AccessError


@tagged('post_install', '-at_install')
class TestAccountMove(TransactionCase):
    """Test suite for AccountMove document scanning, status polling, and feedback actions."""

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param('eagle_doc.api_key', 'test_api_key_12345')
        self.env.company.eagle_sub_business_id = 'sub_bus_123'
        self.partner = self.env['res.partner'].create({
            'name': 'Sample Supplier',
            'supplier_rank': 1,
        })
        self.move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'eagle_doc_sub_business_id': 'sub_bus_123',
            'eagle_doc_task_id': 'task_123',
        })

    def test_01_action_scan_via_eagle_doc_invalid_extension(self):
        """Verify action_scan_via_eagle_doc rejects unsupported file extensions."""
        with self.assertRaises(UserError):
            self.env['account.move'].action_scan_via_eagle_doc(
                filename='test_file.txt',
                file_data='dGVzdA==',
                move_type='in_invoice',
            )

    def test_02_action_scan_via_eagle_doc_missing_api_key(self):
        """Verify action_scan_via_eagle_doc raises error if API key is not configured."""
        self.env['ir.config_parameter'].sudo().set_param('eagle_doc.api_key', False)
        with self.assertRaises(UserError):
            self.env['account.move'].action_scan_via_eagle_doc(
                filename='test_invoice.pdf',
                file_data='dGVzdA==',
                move_type='in_invoice',
            )

    @patch('odoo.addons.eagle_doc_connector.models.account_move.EagleDocAPI.get_processed_document')
    @patch('odoo.addons.eagle_doc_connector.models.account_move.EagleDocAPI.get_invoice_status')
    @patch('odoo.addons.eagle_doc_connector.models.account_move.EagleDocAPI.upload_invoice')
    def test_03_action_scan_via_eagle_doc_success(self, mock_upload, mock_status, mock_document):
        """Verify complete scanning workflow with mocked API endpoints."""
        mock_upload.return_value = {'taskId': 'task_999', 'status': 'PROCESSING'}
        mock_status.return_value = {'status': 'PROCESSED', 'documentId': 'doc_888'}
        mock_document.return_value = {
            'general': {
                'CustomerName': {'value': 'Sample Supplier'},
                'InvoiceNumber': {'value': 'INV-2026-001'},
                'InvoiceDate': {'value': '2026-08-01'},
            }
        }

        res = self.env['account.move'].action_scan_via_eagle_doc(
            filename='invoice_test.pdf',
            file_data='dGVzdA==',
            move_type='in_invoice',
        )

        self.assertEqual(res.get('res_model'), 'account.move')
        created_move = self.env['account.move'].browse(res.get('res_id'))
        self.assertEqual(created_move.eagle_doc_task_id, 'task_999')
        self.assertEqual(created_move.eagle_doc_document_id, 'doc_888')
        self.assertEqual(created_move.eagle_doc_status, 'processed')
        self.assertEqual(created_move.ref, 'INV-2026-001')

    @patch('odoo.addons.eagle_doc_connector.models.account_move.EagleDocAPI.submit_vendor_feedback')
    def test_04_action_eagle_doc_submit_vendor_feedback(self, mock_feedback):
        """Verify submitting vendor feedback to Eagle Doc API."""
        mock_feedback.return_value = {
            'outcome': 'ACCEPTED',
            'accountNumber': 'ACC-1001',
        }

        self.move.eagle_doc_raw_extraction = json.dumps({
            'general': {
                'CustomerName': {'value': 'Old Supplier Name'},
                'BK_CustomerAccountNumber': {'value': 'OLD-ACC-000'},
            }
        })

        res = self.move.action_eagle_doc_submit_vendor_feedback(
            new_vendor_name='Corrected Vendor Name',
            new_vendor_account='ACC-1001',
        )

        self.assertEqual(res.get('outcome'), 'ACCEPTED')
        mock_feedback.assert_called_once()

    @patch('odoo.addons.eagle_doc_connector.models.account_move.EagleDocAPI.submit_product_feedback')
    def test_05_action_eagle_doc_submit_product_feedback(self, mock_feedback):
        """Verify submitting product/account feedback to Eagle Doc API."""
        mock_feedback.return_value = {
            'outcome': 'ACCEPTED',
            'accountNumber': '4400',
            'taxCode': '19',
        }

        self.move.eagle_doc_raw_extraction = json.dumps({
            'general': {'CustomerName': {'value': 'Sample Supplier'}},
            'productItems': [{
                'ProductName': {'value': 'Widget A'},
                'BK_Account': {'value': '4000'},
                'BK_TaxKey': {'value': '7'},
            }]
        })

        res = self.move.action_eagle_doc_submit_product_feedback(
            new_vendor_name='Sample Supplier',
            new_bk_account_number='4400',
            new_product_name='Widget A',
            new_tax_code='19',
        )

        self.assertEqual(res.get('outcome'), 'ACCEPTED')
        mock_feedback.assert_called_once()

    def test_06_apply_eagle_doc_extraction(self):
        """Verify applying raw extraction JSON populates move fields."""
        company_currency = self.env.company.currency_id.name
        doc_data = {
            'general': {
                'CustomerName': {'value': 'Sample Supplier'},
                'InvoiceNumber': {'value': 'INV-9876'},
                'InvoiceDate': {'value': '2026-07-15'},
                'Currency': {'value': company_currency},
            }
        }
        self.move._apply_eagle_doc_extraction(doc_data)

        self.assertEqual(self.move.ref, 'INV-9876')
        self.assertEqual(str(self.move.invoice_date), '2026-07-15')
        self.assertEqual(self.move.currency_id.name, company_currency)
