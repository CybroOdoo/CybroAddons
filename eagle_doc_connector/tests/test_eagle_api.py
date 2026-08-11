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
from odoo.exceptions import UserError
from odoo.addons.eagle_doc_connector.models.eagle_api import EagleDocAPI


@tagged('post_install', '-at_install')
class TestEagleDocAPI(TransactionCase):
    """Test suite for EagleDocAPI REST client methods and error handling."""

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().set_param('eagle_doc.api_key', 'test_api_key_12345')
        self.env['ir.config_parameter'].sudo().set_param('eagle_doc.base_url', 'https://api.test-eagle-doc.com')
        self.api = EagleDocAPI(self.env)
        self.company = self.env.company

    def test_01_headers_and_initialization(self):
        """Verify header generation with and without idempotency key."""
        headers = self.api._get_headers()
        self.assertEqual(headers.get("X-Partner-Api-Key"), 'test_api_key_12345')
        self.assertEqual(headers.get("Accept"), "application/json")
        self.assertNotIn("Idempotency-Key", headers)

        headers_idempotent = self.api._get_headers(idempotency_key="idemp-123")
        self.assertEqual(headers_idempotent.get("Idempotency-Key"), "idemp-123")

    def test_02_missing_api_key_raises_error(self):
        """Verify UserError is raised when API key parameter is not configured."""
        self.env['ir.config_parameter'].sudo().set_param('eagle_doc.api_key', False)
        api = EagleDocAPI(self.env)
        with self.assertRaises(UserError):
            api._get_headers()

    def test_03_extract_error_message(self):
        """Verify error message extraction from HTTP response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": "INVALID_KEY", "message": "API key is invalid"}
        mock_error = MagicMock()
        mock_error.response = mock_response

        msg = self.api._extract_error_message(mock_error)
        self.assertEqual(msg, "INVALID_KEY: API key is invalid")

    @patch('requests.post')
    def test_04_get_or_create_default_sub_business_existing(self, mock_post):
        """Verify existing company sub-business ID is returned without extra API call."""
        self.company.eagle_sub_business_id = 'sub_bus_existing_001'
        sub_id = self.api.get_or_create_default_sub_business()
        self.assertEqual(sub_id, 'sub_bus_existing_001')
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_05_get_or_create_default_sub_business_new(self, mock_post):
        """Verify new sub-business creation when company is not yet linked."""
        self.company.eagle_sub_business_id = False
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "sub_bus_new_999"}
        mock_post.return_value = mock_response

        sub_id = self.api.get_or_create_default_sub_business()
        self.assertEqual(sub_id, "sub_bus_new_999")
        self.assertEqual(self.company.eagle_sub_business_id, "sub_bus_new_999")

    @patch('requests.post')
    def test_06_upload_invoice_success(self, mock_post):
        """Verify invoice document upload formatting and response."""
        attachment = self.env['ir.attachment'].create({
            'name': 'invoice.pdf',
            'datas': 'dGVzdCBjb250ZW50',  # base64 encoded 'test content'
            'mimetype': 'application/pdf',
        })
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"taskId": "task_abc_123", "status": "PROCESSING"}
        mock_post.return_value = mock_response

        res = self.api.upload_invoice("sub_bus_001", attachment, doc_type="INCOMING_INVOICE")
        self.assertEqual(res.get("taskId"), "task_abc_123")
        mock_post.assert_called_once()

    @patch('requests.get')
    def test_07_get_invoice_status(self, mock_get):
        """Verify checking task status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "PROCESSED", "documentId": "doc_999"}
        mock_get.return_value = mock_response

        res = self.api.get_invoice_status("sub_bus_001", "task_abc_123")
        self.assertEqual(res.get("status"), "PROCESSED")
        self.assertEqual(res.get("documentId"), "doc_999")

    @patch('requests.post')
    def test_08_sync_vendor_customers_batch(self, mock_post):
        """Verify vendor/customer batch synchronization request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"created": 1, "updated": 0, "failed": 0, "results": [{"outcome": "CREATED"}]}
        mock_post.return_value = mock_response

        items = [{
            "externalRef": "odoo-partner-1",
            "accountNumber": "VAT123",
            "companyName": "Test Vendor",
            "type": "VENDOR",
        }]
        res = self.api.sync_vendor_customers_batch("sub_bus_001", items)
        self.assertEqual(res.get("created"), 1)

    @patch('requests.get')
    def test_09_get_usage(self, mock_get):
        """Verify fetching billing usage data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "period": "2026-08",
            "totals": {"OCR": 15, "BOOKKEEPING": 10}
        }
        mock_get.return_value = mock_response

        usage = self.api.get_usage(period="2026-08")
        self.assertEqual(usage.get("period"), "2026-08")
        self.assertEqual(usage["totals"]["OCR"], 15)
