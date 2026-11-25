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
#############################################################################
import base64
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestOraFile(TransactionCase):
    """Unit tests for Ora File knowledge base synchronization."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        icp = cls.env['ir.config_parameter'].sudo()
        if hasattr(icp, 'set_str'):
            icp.set_str('ora_ai_base.vapi_private_api_key', 'test_private_key_file')
            icp.set_str('ora_ai_base.vapi_public_api_key', 'test_public_key_file')
            icp.set_str('ora_ai_base.vapi_webhook_base_url', 'https://test-voice.example.com')
        elif hasattr(icp, 'set_param'):
            icp.set_param('ora_ai_base.vapi_private_api_key', 'test_private_key_file')
            icp.set_param('ora_ai_base.vapi_public_api_key', 'test_public_key_file')
            icp.set_param('ora_ai_base.vapi_webhook_base_url', 'https://test-voice.example.com')

    def setUp(self):
        super().setUp()
        icp = self.env['ir.config_parameter'].sudo()
        if hasattr(icp, 'set_str'):
            icp.set_str('ora_ai_base.vapi_private_api_key', 'test_private_key_file')
            icp.set_str('ora_ai_base.vapi_public_api_key', 'test_public_key_file')
            icp.set_str('ora_ai_base.vapi_webhook_base_url', 'https://test-voice.example.com')
        elif hasattr(icp, 'set_param'):
            icp.set_param('ora_ai_base.vapi_private_api_key', 'test_private_key_file')
            icp.set_param('ora_ai_base.vapi_public_api_key', 'test_public_key_file')
            icp.set_param('ora_ai_base.vapi_webhook_base_url', 'https://test-voice.example.com')

    def test_01_detect_mime_type_and_filename_pdf(self):
        """Test MIME sniffing for PDF file with magic header."""
        pdf_bytes = b"%PDF-1.4 sample pdf content for knowledge base"
        ora_file = self.env['ora.file'].new({
            'name': 'Company Handbook',
        })
        name, mime = ora_file._detect_mime_type_and_filename(pdf_bytes)
        self.assertEqual(mime, 'application/pdf')
        self.assertTrue(name.endswith('.pdf'))

    def test_02_detect_mime_type_and_filename_docx(self):
        """Test MIME sniffing for DOCX/ZIP magic header."""
        docx_bytes = b"PK\x03\x04 sample docx archive content"
        ora_file = self.env['ora.file'].new({
            'name': 'Return Policy',
        })
        name, mime = ora_file._detect_mime_type_and_filename(docx_bytes)
        self.assertEqual(mime, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        self.assertTrue(name.endswith('.docx'))

    def test_03_detect_mime_type_text_files(self):
        """Test plain text, CSV, and markdown MIME sniffing."""
        ora_file = self.env['ora.file'].new({
            'name': 'faq_data.csv',
        })
        csv_bytes = b"question,answer\nWhat is your warranty?,2 years"
        name, mime = ora_file._detect_mime_type_and_filename(csv_bytes)
        self.assertEqual(mime, 'text/csv')
        self.assertEqual(name, 'faq_data.csv')

        json_bytes = b'{"name": "test"}'
        ora_file_json = self.env['ora.file'].new({'name': 'data.json'})
        name_j, mime_j = ora_file_json._detect_mime_type_and_filename(json_bytes)
        self.assertEqual(mime_j, 'application/json')

        md_bytes = b'# Title\nDescription'
        ora_file_md = self.env['ora.file'].new({'name': 'readme.md'})
        name_m, mime_m = ora_file_md._detect_mime_type_and_filename(md_bytes)
        self.assertEqual(mime_m, 'text/markdown')

    def test_04_file_size_validation_exceeded(self):
        """Test that file exceeding MAX_FILE_SIZE raises UserError."""
        # 26 MB of dummy data
        oversized = base64.b64encode(b"X" * (26 * 1024 * 1024)).decode('utf-8')
        with self.assertRaises(UserError):
            self.env['ora.file'].create({
                'name': 'Oversized Document',
                'file': oversized,
                'filename': 'large.pdf'
            })

    @patch('requests.post')
    def test_05_upload_file_to_vapi_success(self, mock_post):
        """Test successful file upload and registration with Vapi API."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'vapi_file_doc_456',
            'name': 'Company Guidelines.pdf',
            'status': 'indexed'
        }
        mock_post.return_value = mock_response

        dummy_pdf = base64.b64encode(b"%PDF-1.4 test guidelines").decode('utf-8')
        file_record = self.env['ora.file'].create({
            'name': 'Company Guidelines',
            'file': dummy_pdf,
            'filename': 'Company Guidelines.pdf',
        })

        self.assertEqual(file_record.id_file, 'vapi_file_doc_456')
        self.assertEqual(file_record.state, 'uploaded')
        self.assertTrue(mock_post.called)

    @patch('requests.delete')
    @patch('requests.post')
    def test_06_unlink_removes_vapi_file(self, mock_post, mock_delete):
        """Test that unlinking local file deletes remote file on Vapi."""
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 201
        mock_post_resp.json.return_value = {'id': 'vapi_file_to_del'}
        mock_post.return_value = mock_post_resp

        mock_del_resp = MagicMock()
        mock_del_resp.status_code = 200
        mock_delete.return_value = mock_del_resp

        dummy_txt = base64.b64encode(b"Some text to delete").decode('utf-8')
        file_record = self.env['ora.file'].create({
            'name': 'Temp Notes',
            'file': dummy_txt,
            'filename': 'Temp Notes.txt',
        })
        file_record.unlink()
        self.assertTrue(mock_delete.called)

    def test_07_extract_raw_bytes_helpers(self):
        """Test static raw byte extractor with various formats."""
        res_empty = self.env['ora.file']._extract_raw_bytes(False)
        self.assertEqual(res_empty, b'')

        encoded_str = base64.b64encode(b"hello world").decode('ascii')
        res_bytes = self.env['ora.file']._extract_raw_bytes(encoded_str)
        self.assertEqual(res_bytes, b"hello world")

    def test_08_detect_mime_type_legacy_doc(self):
        """Test sniffing legacy Word doc format."""
        doc_bytes = b"\xd0\xcf\x11\xe0 sample doc"
        ora_file = self.env['ora.file'].new({'name': 'old_doc.doc'})
        name, mime = ora_file._detect_mime_type_and_filename(doc_bytes)
        self.assertEqual(mime, 'application/msword')
        self.assertTrue(name.endswith('.doc'))

    def test_09_upload_without_api_key_raises(self):
        """Test that attempting to upload without API key raises UserError."""
        icp = self.env['ir.config_parameter'].sudo()
        old_val = getattr(icp, 'get_str', getattr(icp, 'get_param', lambda k: ''))('ora_ai_base.vapi_private_api_key')
        if hasattr(icp, 'set_str'):
            icp.set_str('ora_ai_base.vapi_private_api_key', '')
        elif hasattr(icp, 'set_param'):
            icp.set_param('ora_ai_base.vapi_private_api_key', '')

        file_rec = self.env['ora.file'].new({
            'name': 'No Key File',
            'file': base64.b64encode(b"test").decode('ascii'),
        })
        with self.assertRaises(UserError):
            file_rec.action_upload_to_vapi()

        # Restore
        if hasattr(icp, 'set_str'):
            icp.set_str('ora_ai_base.vapi_private_api_key', old_val or 'test_private_key_file')
        elif hasattr(icp, 'set_param'):
            icp.set_param('ora_ai_base.vapi_private_api_key', old_val or 'test_private_key_file')

    @patch('requests.post')
    def test_10_upload_failure_handling(self, mock_post):
        """Test handling failed upload response from Vapi."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'message': 'Invalid file format'}
        mock_post.return_value = mock_response

        dummy_data = base64.b64encode(b"%PDF-1.4 failed upload").decode('ascii')
        file_rec = self.env['ora.file'].create({
            'name': 'Failed Doc',
            'file': dummy_data,
            'filename': 'failed.pdf',
        })
        self.assertEqual(file_rec.state, 'error')
        self.assertIn('Invalid file format', file_rec.error_message)

    @patch('requests.patch')
    @patch('requests.post')
    def test_11_write_file_renames_on_vapi(self, mock_post, mock_patch):
        """Test that updating filename triggers remote name patch on Vapi."""
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {'id': 'vapi_doc_rename'}
        mock_patch.return_value.status_code = 200

        dummy_data = base64.b64encode(b"%PDF-1.4 file content").decode('ascii')
        file_rec = self.env['ora.file'].create({
            'name': 'Original Name',
            'file': dummy_data,
            'filename': 'original.pdf',
        })
        file_rec.write({'name': 'Updated Name'})
        self.assertEqual(file_rec.name, 'Updated Name')
        self.assertTrue(mock_patch.called)

    @patch('requests.delete')
    @patch('requests.post')
    def test_12_reupload_deletes_old_file_and_fallback_sniffing(self, mock_post, mock_del):
        """Test re-uploading file deletes old Vapi file and test extensionless fallbacks."""
        mock_post.return_value.status_code = 201
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {'id': 'vapi_new_file_id'}
        mock_del.return_value.status_code = 200

        dummy_data = base64.b64encode(b"Some plain text content").decode('ascii')
        file_rec = self.env['ora.file'].create({
            'name': 'plain_note',
            'file': dummy_data,
        })
        # Test extension added to plain note
        name, mime = file_rec._detect_mime_type_and_filename(b"Some plain text content")
        self.assertEqual(mime, 'text/plain')
        self.assertTrue(name.endswith('.txt'))

        # Set id_file to simulate pre-existing remote file
        file_rec.id_file = 'vapi_old_file_id'
        file_rec.action_upload_to_vapi()
        self.assertTrue(mock_del.called)
        self.assertEqual(file_rec.id_file, 'vapi_new_file_id')
        self.assertEqual(file_rec.state, 'uploaded')

    @patch('requests.delete')
    @patch('requests.request')
    @patch('requests.post')
    def test_13_upload_empty_file_and_linked_assistant_sync(self, mock_post, mock_req, mock_del):
        """Test uploading empty file and syncing linked assistants."""
        mock_post.return_value.status_code = 201
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {'id': 'vapi_file_sync_1'}
        mock_req.return_value.status_code = 200
        mock_req.return_value.ok = True
        mock_del.return_value.status_code = 200
        mock_del.return_value.ok = True

        # Test empty file state error
        empty_rec = self.env['ora.file'].create({
            'name': 'empty.txt',
            'file': False,
        })
        self.assertEqual(empty_rec.state, 'draft')

        # Test linked assistant sync
        content = base64.b64encode(b"FAQ Knowledge Base").decode('ascii')
        file_rec = self.env['ora.file'].create({
            'name': 'faq.txt',
            'file': content,
        })
        asst = self.env['ora.ai'].search([], limit=1)
        if asst:
            asst.write({'file_ids': [(4, file_rec.id)], 'id_assistant': 'vapi_asst_mock_sync'})
            file_rec.action_upload_to_vapi()
            self.assertTrue(file_rec.id_file)


