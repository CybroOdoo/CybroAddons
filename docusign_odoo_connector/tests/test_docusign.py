# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..models import docusign


@tagged('post_install', '-at_install')
class TestDocuSignAPI(TransactionCase):
    """Unit tests for DocuSign API wrapper functions in models/docusign.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pem_key = (
            b"-----BEGIN RSA PRIVATE KEY-----\n"
            b"MIIEowIBAAKCAQEA0Y3...\n"
            b"-----END RSA PRIVATE KEY-----\n"
        )
        cls.b64_pem_key = base64.b64encode(cls.pem_key).decode('ascii')
        cls.test_attachment = cls.env['ir.attachment'].create({
            'name': 'test_private_key.pem',
            'type': 'binary',
            'raw': cls.pem_key,
        })
        cls.test_attachment_b64 = cls.env['ir.attachment'].create({
            'name': 'test_private_key_b64.pem',
            'type': 'binary',
            'raw': cls.b64_pem_key,
        })

    def setUp(self):
        super().setUp()
        docusign._TOKEN_CACHE.clear()

    def test_01_get_private_key_bytes_empty(self):
        """Test _get_private_key_bytes with empty or None values."""
        self.assertEqual(docusign._get_private_key_bytes(None), b'')
        self.assertEqual(docusign._get_private_key_bytes(False), b'')
        self.assertEqual(docusign._get_private_key_bytes(""), b'')
        self.assertEqual(docusign._get_private_key_bytes([]), b'')

    def test_02_get_private_key_bytes_attachment_raw(self):
        """Test _get_private_key_bytes with ir.attachment having raw bytes."""
        result = docusign._get_private_key_bytes(self.test_attachment)
        self.assertEqual(result, self.pem_key)

    def test_03_get_private_key_bytes_attachment_datas(self):
        """Test _get_private_key_bytes with ir.attachment having datas field."""
        result = docusign._get_private_key_bytes(self.test_attachment_b64)
        self.assertEqual(result, self.pem_key)

    def test_04_get_private_key_bytes_raw_bytes_and_str(self):
        """Test _get_private_key_bytes with raw bytes and string."""
        self.assertEqual(docusign._get_private_key_bytes(self.pem_key), self.pem_key)
        self.assertEqual(
            docusign._get_private_key_bytes(self.pem_key.decode('utf-8')),
            self.pem_key
        )

    def test_05_get_private_key_bytes_b64_encoded(self):
        """Test _get_private_key_bytes with base64 encoded PEM."""
        result = docusign._get_private_key_bytes(self.b64_pem_key.encode('utf-8'))
        self.assertEqual(result, self.pem_key)

    @patch.object(docusign, 'ApiClient')
    def test_06_get_docusign_access_token_and_cache(self, mock_api_client_cls):
        """Test access token retrieval and subsequent cached hit."""
        mock_client = MagicMock()
        mock_api_client_cls.return_value = mock_client
        mock_token_obj = MagicMock()
        mock_token_obj.access_token = "mock_jwt_access_token_123"
        mock_client.request_jwt_user_token.return_value = mock_token_obj

        # 1. Fresh retrieval
        token = docusign.get_docusign_access_token("client_1", "user_1", self.pem_key)
        self.assertEqual(token, "mock_jwt_access_token_123")
        self.assertEqual(mock_client.request_jwt_user_token.call_count, 1)

        # 2. Subsequent call should hit cache without calling request_jwt_user_token again
        cached_token = docusign.get_docusign_access_token("client_1", "user_1", self.pem_key)
        self.assertEqual(cached_token, "mock_jwt_access_token_123")
        self.assertEqual(mock_client.request_jwt_user_token.call_count, 1)

    @patch.object(docusign, 'get_docusign_access_token', return_value="mock_jwt_access_token_123")
    @patch.object(docusign, 'ApiClient')
    def test_07_get_authenticated_api_client(self, mock_api_client_cls, mock_get_token):
        """Test get_authenticated_api_client sets Bearer token."""
        mock_client = MagicMock()
        mock_api_client_cls.return_value = mock_client

        client = docusign.get_authenticated_api_client("client_1", "user_1", self.pem_key)
        self.assertEqual(client, mock_client)
        mock_client.set_default_header.assert_called_once_with(
            header_name="Authorization",
            header_value="Bearer mock_jwt_access_token_123"
        )

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    @patch.object(docusign, 'get_docusign_access_token', return_value="mock_jwt_access_token")
    @patch.object(docusign.requests, 'get')
    def test_08_action_login_docusign_success(self, mock_requests_get, mock_get_token, mock_envelopes_api_cls, mock_get_client):
        """Test action_login_docusign returns status code 200 on success."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response

        status = docusign.action_login_docusign("user_1", "acc_1", "client_1", self.pem_key)
        self.assertEqual(status, 200)

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    def test_09_action_login_docusign_api_exception(self, mock_envelopes_api_cls, mock_get_client):
        """Test action_login_docusign raises UserError when ApiException is encountered."""
        mock_api = MagicMock()
        mock_envelopes_api_cls.return_value = mock_api
        exc = docusign.ApiException(status=401, reason="Invalid credentials")
        exc.trace_token = "mock_trace"
        exc.timestamp = "mock_timestamp"
        mock_api.list_status_changes.side_effect = exc

        with self.assertRaises(UserError):
            docusign.action_login_docusign("user_1", "acc_1", "client_1", self.pem_key)

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    def test_10_action_send_docusign_file_success(self, mock_envelopes_api_cls, mock_get_client):
        """Test action_send_docusign_file creates envelope and adjusts tabs."""
        mock_api = MagicMock()
        mock_envelopes_api_cls.return_value = mock_api
        mock_response = MagicMock()
        mock_response.envelope_id = "mock_envelope_abc"
        mock_response.status = "sent"
        mock_api.create_envelope.return_value = mock_response

        tabs = [{
            'recipient': 'John Doe',
            'signHereTabs': [{'xPosition': 100, 'yPosition': 150}],
        }]
        response = docusign.action_send_docusign_file(
            user_id="user_1",
            account_id="acc_1",
            integratorKey="client_1",
            privatekey=self.pem_key,
            filename="Contract.pdf",
            fileContents=b"%PDF-1.4 test content",
            receiver_name=["John Doe"],
            receiver_email=["john@example.com"],
            tabs1=tabs,
            webhook_url="https://example.com/docusign/webhook"
        )
        self.assertEqual(response.envelope_id, "mock_envelope_abc")
        self.assertEqual(response.status, "sent")
        mock_api.create_envelope.assert_called_once()
        # Verify yPosition was adjusted by max(0, y - 30): 150 - 30 = 120
        call_args = mock_api.create_envelope.call_args
        envelope_def = call_args.kwargs.get('envelope_definition')
        signer = envelope_def.recipients.signers[0]
        self.assertEqual(signer['tabs']['signHereTabs'][0]['yPosition'], 120)

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    def test_11_action_send_docusign_file_api_exception(self, mock_envelopes_api_cls, mock_get_client):
        """Test action_send_docusign_file raises UserError on ApiException."""
        mock_api = MagicMock()
        mock_envelopes_api_cls.return_value = mock_api
        exc = docusign.ApiException(status=400, reason="Failed to send envelope")
        exc.trace_token = "mock_trace"
        exc.timestamp = "mock_timestamp"
        mock_api.create_envelope.side_effect = exc

        with self.assertRaises(UserError):
            docusign.action_send_docusign_file(
                user_id="user_1",
                account_id="acc_1",
                integratorKey="client_1",
                privatekey=self.pem_key,
                filename="Contract.pdf",
                fileContents=b"%PDF-1.4 test",
                receiver_name=["John Doe"],
                receiver_email=["john@example.com"],
                tabs1=None
            )

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    def test_12_download_documents_not_completed(self, mock_envelopes_api_cls, mock_get_client):
        """Test download_documents when document is not yet completed."""
        mock_api = MagicMock()
        mock_envelopes_api_cls.return_value = mock_api
        mock_env_info = MagicMock()
        mock_env_info.status = "sent"
        mock_api.get_envelope.return_value = mock_env_info

        status, path = docusign.download_documents("client_1", "env_1", self.pem_key, "user_1", "acc_1")
        self.assertEqual(status, "sent")
        self.assertEqual(path, '')

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    def test_13_download_documents_completed(self, mock_envelopes_api_cls, mock_get_client):
        """Test download_documents when document is completed."""
        mock_api = MagicMock()
        mock_envelopes_api_cls.return_value = mock_api
        mock_env_info = MagicMock()
        mock_env_info.status = "completed"
        mock_api.get_envelope.return_value = mock_env_info

        mock_doc = MagicMock()
        mock_doc.name = "SignedAgreement.pdf"
        mock_docs_res = MagicMock()
        mock_docs_res.envelope_documents = [mock_doc]
        mock_api.list_documents.return_value = mock_docs_res

        pdf_content = b"%PDF-1.4 Mock signed document content"
        mock_api.get_document.return_value = pdf_content

        status, path = docusign.download_documents("client_1", "env_1", self.pem_key, "user_1", "acc_1")
        try:
            self.assertEqual(status, "completed")
            self.assertTrue(os.path.exists(path))
            with open(path, "rb") as f:
                self.assertEqual(f.read(), pdf_content)
        finally:
            if os.path.exists(path):
                os.remove(path)
            folder = os.path.dirname(path)
            if os.path.exists(folder):
                shutil.rmtree(folder)

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    def test_14_get_status_success_and_exception(self, mock_envelopes_api_cls, mock_get_client):
        """Test get_status returns status and raises UserError on ApiException."""
        mock_api = MagicMock()
        mock_envelopes_api_cls.return_value = mock_api
        mock_env_info = MagicMock()
        mock_env_info.status = "delivered"
        mock_api.get_envelope.return_value = mock_env_info

        status = docusign.get_status("client_1", "env_1", self.pem_key, "user_1", "acc_1")
        self.assertEqual(status, "delivered")

        exc = docusign.ApiException(status=400, reason="Status error")
        exc.trace_token = "mock_trace"
        exc.timestamp = "mock_timestamp"
        mock_api.get_envelope.side_effect = exc
        with self.assertRaises(UserError):
            docusign.get_status("client_1", "env_1", self.pem_key, "user_1", "acc_1")

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    def test_15_action_send_docusign_file_clamps_out_of_bounds_tabs(self, mock_envelopes_api_cls, mock_get_client):
        """Test action_send_docusign_file clamps out-of-bounds tab coordinates to PDF page bounds."""
        mock_api = MagicMock()
        mock_envelopes_api_cls.return_value = mock_api
        mock_response = MagicMock()
        mock_response.envelope_id = "mock_envelope_clamp"
        mock_response.status = "sent"
        mock_api.create_envelope.return_value = mock_response

        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Page /MediaBox [0 0 612 792] >>\nendobj\n"
        tabs = [{
            'recipient': 'OpenWood',
            'companyTabs': [{'xPosition': 750, 'yPosition': 900, 'pageNumber': '1'}],
        }]
        docusign.action_send_docusign_file(
            user_id="user_1",
            account_id="acc_1",
            integratorKey="client_1",
            privatekey=self.pem_key,
            filename="INV_2025_00021.pdf",
            fileContents=pdf_bytes,
            receiver_name=["OpenWood"],
            receiver_email=["openwood@example.com"],
            tabs1=tabs,
        )
        envelope_def = mock_api.create_envelope.call_args.kwargs.get('envelope_definition')
        company_tab = envelope_def.recipients.signers[0]['tabs']['companyTabs'][0]
        self.assertLessEqual(company_tab['xPosition'], 612 - 180)
        self.assertLessEqual(company_tab['yPosition'], 792 - 50)

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    def test_16_action_send_docusign_file_uses_actual_extension(self, mock_envelopes_api_cls, mock_get_client):
        """Test action_send_docusign_file sets file_extension from filename."""
        mock_api = MagicMock()
        mock_envelopes_api_cls.return_value = mock_api
        mock_response = MagicMock()
        mock_response.envelope_id = "mock_envelope_xlsx"
        mock_response.status = "sent"
        mock_api.create_envelope.return_value = mock_response

        docusign.action_send_docusign_file(
            user_id="user_1",
            account_id="acc_1",
            integratorKey="client_1",
            privatekey=self.pem_key,
            filename="Journal Item (account.move.line) (2).xlsx",
            fileContents=b"PK\x03\x04mock_xlsx_content",
            receiver_name=["OpenWood"],
            receiver_email=["openwood@example.com"],
            tabs1=None,
        )
        envelope_def = mock_api.create_envelope.call_args.kwargs.get('envelope_definition')
        self.assertEqual(envelope_def.documents[0].file_extension, 'xlsx')

    def test_17_get_pdf_page_dimensions_and_clamp_user_tabs(self):
        """Test _get_pdf_page_dimensions and _clamp_user_tabs helpers directly."""
        default_dims = docusign._get_pdf_page_dimensions(b"")
        self.assertEqual(default_dims['default'], (595.0, 792.0))

        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /MediaBox [0 0 612 792] >>\nendobj\n"
        dims = docusign._get_pdf_page_dimensions(pdf_bytes)
        self.assertEqual(dims[1], (612.0, 792.0))

        user_tabs = {
            'signHereTabs': [{'xPosition': 900, 'yPosition': 1000, 'pageNumber': '1'}],
            'companyTabs': [{'xPosition': -10, 'yPosition': 950, 'pageNumber': '1'}],
        }
        docusign._clamp_user_tabs(user_tabs, dims)
        self.assertEqual(user_tabs['signHereTabs'][0]['xPosition'], 612 - 100)
        self.assertEqual(user_tabs['signHereTabs'][0]['yPosition'], 792 - 50)
        self.assertEqual(user_tabs['companyTabs'][0]['xPosition'], 0)
        self.assertEqual(user_tabs['companyTabs'][0]['yPosition'], 792 - 50)

    def test_18_get_docusign_endpoints(self):
        """Test _get_docusign_endpoints returns appropriate URLs for demo and production."""
        demo_rest, demo_oauth = docusign._get_docusign_endpoints('demo')
        self.assertEqual(demo_rest, 'https://demo.docusign.net/restapi')
        self.assertEqual(demo_oauth, 'account-d.docusign.com')

        prod_rest, prod_oauth = docusign._get_docusign_endpoints('production')
        self.assertEqual(prod_rest, 'https://www.docusign.net/restapi')
        self.assertEqual(prod_oauth, 'account.docusign.com')

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    def test_19_action_send_docusign_file_filecontents_types_and_event_notification(self, mock_envelopes_api_cls, mock_get_client):
        """Test action_send_docusign_file handles object with to_base64(), string base64, and attaches webhook EventNotification."""
        mock_api = MagicMock()
        mock_envelopes_api_cls.return_value = mock_api
        mock_response = MagicMock()
        mock_response.envelope_id = "mock_envelope_event"
        mock_response.status = "sent"
        mock_api.create_envelope.return_value = mock_response

        # 1. Custom object with to_base64() method
        class MockFileObj:
            def to_base64(self):
                return base64.b64encode(b"%PDF-1.4 Mock ToBase64").decode('ascii')

        response = docusign.action_send_docusign_file(
            user_id="user_1",
            account_id="acc_1",
            integratorKey="client_1",
            privatekey=self.pem_key,
            filename="Document.pdf",
            fileContents=MockFileObj(),
            receiver_name=["Partner One"],
            receiver_email=["partner.one@example.com"],
            tabs1=None,
            webhook_url="https://example.com/docusign/webhook",
        )
        self.assertEqual(response.envelope_id, "mock_envelope_event")
        envelope_def = mock_api.create_envelope.call_args.kwargs.get('envelope_definition')
        self.assertTrue(hasattr(envelope_def, 'event_notification'))

        # 2. String base64 content
        b64_str = base64.b64encode(b"%PDF-1.4 String base64").decode('ascii')
        docusign.action_send_docusign_file(
            user_id="user_1",
            account_id="acc_1",
            integratorKey="client_1",
            privatekey=self.pem_key,
            filename="Document.pdf",
            fileContents=b64_str,
            receiver_name=["Partner One"],
            receiver_email=["partner.one@example.com"],
            tabs1=None,
        )

    @patch.object(docusign, 'get_authenticated_api_client')
    @patch.object(docusign, 'EnvelopesApi')
    def test_20_download_documents_api_and_general_exceptions(self, mock_envelopes_api_cls, mock_get_client):
        """Test download_documents handles ApiException and general Exception by raising UserError."""
        mock_api = MagicMock()
        mock_envelopes_api_cls.return_value = mock_api

        # ApiException
        exc = docusign.ApiException(status=400, reason="DocuSign API failure")
        exc.trace_token = "mock_trace"
        exc.timestamp = "mock_time"
        mock_api.get_envelope.side_effect = exc
        with self.assertRaises(UserError):
            docusign.download_documents("client_1", "env_1", self.pem_key, "user_1", "acc_1")

        # General Exception
        mock_api.get_envelope.side_effect = RuntimeError("Network timeout")
        with self.assertRaises(UserError):
            docusign.download_documents("client_1", "env_1", self.pem_key, "user_1", "acc_1")

    @patch('requests.get')
    @patch.object(docusign, 'get_docusign_access_token', return_value="mock_token")
    @patch.object(docusign, 'EnvelopesApi')
    @patch.object(docusign, 'get_authenticated_api_client')
    def test_21_action_login_docusign_production_environment(self, mock_get_client, mock_envelopes_api_cls, mock_get_token, mock_requests_get):
        """Test action_login_docusign uses production endpoint when environment='production'."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_requests_get.return_value = mock_resp

        status = docusign.action_login_docusign(
            "user_prod", "acc_prod", "client_prod", self.pem_key, environment='production'
        )
        self.assertEqual(status, 200)
        call_url = mock_requests_get.call_args.kwargs.get('url') or mock_requests_get.call_args[1].get('url', '')
        if not call_url and mock_requests_get.call_args[0]:
            call_url = mock_requests_get.call_args[0][0]
        self.assertIn("account.docusign.com", call_url)

    def test_22_get_private_key_bytes_content_attribute(self):
        """Test _get_private_key_bytes handles attachments whose raw field contains an object with a .content attribute."""
        class MockRawWithContent:
            def __init__(self, content):
                self.content = content

        class MockAttachmentWithRawContent:
            def __init__(self, raw):
                self.raw = raw

            def __getitem__(self, item):
                return self

        mock_obj = MockAttachmentWithRawContent(MockRawWithContent(self.pem_key))
        result = docusign._get_private_key_bytes(mock_obj)
        self.assertEqual(result, self.pem_key)
