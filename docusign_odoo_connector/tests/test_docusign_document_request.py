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
import json
import os
import tempfile
from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDocuSignDocumentRequest(TransactionCase):
    """Unit tests for docusign.document.request and line models in models/docusign_document_request.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Customer One',
            'email': 'customer1@example.com',
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Customer Two',
            'email': 'customer2@example.com',
        })
        cls.att_key = cls.env['ir.attachment'].create({
            'name': 'req_key.pem',
            'type': 'binary',
            'raw': b"-----BEGIN RSA PRIVATE KEY-----\nMOCK\n-----END RSA PRIVATE KEY-----",
        })
        cls.credential = cls.env['docusign.credentials'].create({
            'name': 'Request DocuSign Credential',
            'integrator_key': 'int-key-req',
            'account_id_data': 'acc-id-req',
            'user_id_data': 'user-id-req',
            'private_key_ids': [Command.link(cls.att_key.id)],
            'company_id': cls.env.company.id,
        })
        cls.doc_attachment = cls.env['ir.attachment'].create({
            'name': 'Contract.pdf',
            'type': 'binary',
            'raw': b"%PDF-1.4 mock contract content",
            'docusign_tabs': json.dumps([{'recipient': 'Customer One', 'signHere': 'tab'}]),
        })

    def test_01_creation_and_defaults(self):
        """Test default values, sequence number generation and expiry date."""
        req = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'document_ids': [Command.link(self.doc_attachment.id)],
            'credentials_id': self.credential.id,
        })
        self.assertNotEqual(req.name, 'New')
        self.assertEqual(req.state, 'draft')
        self.assertEqual(req.selection_type, 'mandatory')
        today = fields.Date.context_today(self)
        self.assertGreater(req.expiry_date, today)

    def test_02_expiry_date_constraint(self):
        """Test that setting expiry_date in the past raises a ValidationError."""
        yesterday = fields.Date.context_today(self) - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.env['docusign.document.request'].create({
                'company_id': self.env.company.id,
                'partner_ids': [Command.link(self.partner_1.id)],
                'expiry_date': yesterday,
            })

    def test_03_action_draft(self):
        """Test action_draft resets request to draft state."""
        req = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'state': 'sent',
            'reminder_sent': True,
        })
        req.action_draft()
        self.assertEqual(req.state, 'draft')
        self.assertFalse(req.reminder_sent)

    def test_04_onchange_selection_type(self):
        """Test _onchange_selection_type populates custom lines when switched to custom."""
        req = self.env['docusign.document.request'].new({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id), Command.link(self.partner_2.id)],
            'document_ids': [Command.link(self.doc_attachment.id)],
            'selection_type': 'custom',
        })
        req._onchange_selection_type()
        self.assertEqual(len(req.custom_line_ids), 2)
        partners_in_custom = [line.partner_id._origin.id for line in req.custom_line_ids]
        self.assertIn(self.partner_1.id, partners_in_custom)
        self.assertIn(self.partner_2.id, partners_in_custom)

    def test_05_get_document_assignments_mandatory_validation(self):
        """Test validation in _get_document_assignments for mandatory mode."""
        # 1. No partners
        req_no_partners = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [],
            'document_ids': [Command.link(self.doc_attachment.id)],
        })
        with self.assertRaises(UserError):
            req_no_partners._get_document_assignments()

        # 2. No documents
        req_no_docs = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'document_ids': [],
        })
        with self.assertRaises(UserError):
            req_no_docs._get_document_assignments()

        # 3. Partner without email
        partner_no_email = self.env['res.partner'].create({'name': 'No Email Partner'})
        req_no_email = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(partner_no_email.id)],
            'document_ids': [Command.link(self.doc_attachment.id)],
        })
        with self.assertRaises(UserError):
            req_no_email._get_document_assignments()

    def test_06_get_document_assignments_custom_validation(self):
        """Test validation in _get_document_assignments for custom mode."""
        # 1. Custom mode without lines
        req_custom = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'selection_type': 'custom',
            'partner_ids': [Command.link(self.partner_1.id)],
        })
        with self.assertRaises(UserError):
            req_custom._get_document_assignments()

        # 2. Custom line without documents
        line = self.env['docusign.document.request.line'].create({
            'request_id': req_custom.id,
            'partner_id': self.partner_1.id,
            'document_ids': [],
        })
        with self.assertRaises(UserError):
            req_custom._get_document_assignments()

        # 3. Valid custom line
        line.document_ids = [Command.link(self.doc_attachment.id)]
        assignments = req_custom._get_document_assignments()
        self.assertIn(self.partner_1, assignments)
        self.assertEqual(assignments[self.partner_1], self.doc_attachment)

    def test_07_action_open_document_wizard(self):
        """Test action_open_document_wizard returns wizard action."""
        req = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'document_ids': [Command.link(self.doc_attachment.id)],
        })
        action = req.action_open_document_wizard()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'send.document')
        self.assertEqual(action.get('target'), 'new')

    def test_08_action_send_document_missing_tabs_validation(self):
        """Test action_send_document raises UserError if document has no tabs configured."""
        doc_no_tabs = self.env['ir.attachment'].create({
            'name': 'NoTabs.pdf',
            'type': 'binary',
            'raw': b"%PDF-1.4 content",
            'docusign_tabs': False,
        })
        req = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'document_ids': [Command.link(doc_no_tabs.id)],
            'credentials_id': self.credential.id,
        })
        with self.assertRaises(UserError) as cm:
            req.action_send_document()
        self.assertIn('You need to add fields', str(cm.exception))

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.action_send_docusign_file')
    def test_09_action_send_document_success(self, mock_send):
        """Test action_send_document successfully creates docusign.lines and updates state to sent."""
        mock_res = MagicMock()
        mock_res.envelope_id = 'ENV-REQ-SEND-1'
        mock_res.status = 'sent'
        mock_send.return_value = mock_res

        req = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'document_ids': [Command.link(self.doc_attachment.id)],
            'credentials_id': self.credential.id,
        })

        action = req.action_send_document()
        self.assertEqual(req.state, 'sent')
        self.assertEqual(len(req.docusign_line_ids), 1)
        self.assertEqual(req.docusign_line_ids[0].envelope_id, 'ENV-REQ-SEND-1')
        self.assertEqual(action.get('type'), 'ir.actions.client')

    def test_10_update_signing_state(self):
        """Test state transitions based on docusign line statuses."""
        req = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id), Command.link(self.partner_2.id)],
            'state': 'sent',
        })
        line1 = self.env['docusign.lines'].create({
            'request_id': req.id,
            'partner_id': self.partner_1.id,
            'document': 'Doc1.pdf',
            'status': 'sent',
        })
        line2 = self.env['docusign.lines'].create({
            'request_id': req.id,
            'partner_id': self.partner_2.id,
            'document': 'Doc2.pdf',
            'status': 'sent',
        })

        # When none are completed
        req._update_signing_state()
        self.assertEqual(req.state, 'sent')

        # When one is completed -> partially_signed
        line1.status = 'completed'
        req._update_signing_state()
        self.assertEqual(req.state, 'partially_signed')

        # When both are completed -> fully_signed
        line2.status = 'completed'
        req._update_signing_state()
        self.assertEqual(req.state, 'fully_signed')

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.download_documents')
    def test_11_sync_document_status_and_download(self, mock_download):
        """Test _sync_document_status downloads completed document and updates state."""
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, 'SignedContract.pdf')
        with open(temp_file_path, 'wb') as f:
            f.write(b"%PDF-1.4 Mock signed PDF")

        mock_download.return_value = ('completed', temp_file_path)

        req = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'credentials_id': self.credential.id,
            'state': 'sent',
        })
        line = self.env['docusign.lines'].create({
            'request_id': req.id,
            'partner_id': self.partner_1.id,
            'document': 'Contract.pdf',
            'envelope_id': 'ENV-SYNC-001',
            'status': 'sent',
        })

        req._sync_document_status(target_envelope_id='ENV-SYNC-001')

        self.assertEqual(line.status, 'completed')
        self.assertTrue(line.signed_document)
        self.assertEqual(req.state, 'fully_signed')

        # Verify attachment was created and de-duplicated
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'docusign.document.request'),
            ('res_id', '=', req.id),
            ('name', '=', 'SignedContract.pdf'),
        ])
        self.assertEqual(len(attachments), 1)

        # Re-running sync skips already completed/signed lines and preserves single attachment
        req._sync_document_status(target_envelope_id='ENV-SYNC-001')
        attachments_after = self.env['ir.attachment'].search([
            ('res_model', '=', 'docusign.document.request'),
            ('res_id', '=', req.id),
            ('name', '=', 'SignedContract.pdf'),
        ])
        self.assertEqual(len(attachments_after), 1)

    def test_12_reminders(self):
        """Test action_send_reminder and _cron_send_signing_reminder."""
        req = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'state': 'draft',
        })
        # Reminders cannot be sent in draft
        with self.assertRaises(UserError):
            req.action_send_reminder()

        req.state = 'sent'
        self.env['docusign.lines'].create({
            'request_id': req.id,
            'partner_id': self.partner_1.id,
            'document': 'Contract.pdf',
            'envelope_id': 'ENV-REMIND-01',
            'status': 'sent',
        })

        res = req.action_send_reminder()
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertTrue(req.reminder_sent)

        # Test cron execution
        req.reminder_sent = False
        today = fields.Date.context_today(self)
        req.expiry_date = today + timedelta(days=2)
        self.env['docusign.document.request']._cron_send_signing_reminder()
        self.assertTrue(req.reminder_sent)

    def test_13_cron_auto_update_status(self):
        """Test _cron_auto_update_status triggers sync on active requests."""
        self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'state': 'sent',
        })
        with patch.object(type(self.env['docusign.document.request']), '_sync_document_status') as mock_sync:
            self.env['docusign.document.request']._cron_auto_update_status()
            mock_sync.assert_called()

    def test_14_multi_company_defaults_and_credentials(self):
        """Test _is_multi_company, _default_company_id, _default_credentials_id, default_get, _get_default_credentials, _compute_credentials_id, _onchange_company_id."""
        RequestModel = self.env['docusign.document.request']
        expected_cred = RequestModel._get_default_credentials(self.env.company)
        self.assertTrue(expected_cred)

        with patch.object(type(RequestModel), '_is_multi_company', return_value=False):
            self.assertEqual(RequestModel._default_company_id(), self.env.company)
            self.assertEqual(RequestModel._default_credentials_id(), expected_cred)
            defaults = RequestModel.default_get(['company_id', 'credentials_id'])
            self.assertEqual(defaults.get('company_id'), self.env.company.id)
            self.assertEqual(defaults.get('credentials_id'), expected_cred.id)

        with patch.object(type(RequestModel), '_is_multi_company', return_value=True):
            self.assertFalse(RequestModel._default_company_id())
            self.assertFalse(RequestModel._default_credentials_id())
            defaults_multi = RequestModel.default_get(['company_id', 'credentials_id'])
            self.assertFalse(defaults_multi.get('company_id'))
            self.assertFalse(defaults_multi.get('credentials_id'))

        req = RequestModel.create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
        })
        req._compute_credentials_id()
        self.assertEqual(req.credentials_id, expected_cred)

        req._onchange_company_id()
        self.assertEqual(req.credentials_id, expected_cred)

        other_company = self.env['res.company'].create({'name': 'Other Test Company'})
        req.company_id = other_company
        res = req._onchange_company_id()
        self.assertFalse(req.credentials_id)
        self.assertIn('warning', res)

    def test_15_check_expiry_date_constraint(self):
        """Test _check_expiry_date raises ValidationError for past dates."""
        past_date = fields.Date.context_today(self) - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.env['docusign.document.request'].create({
                'company_id': self.env.company.id,
                'partner_ids': [Command.link(self.partner_1.id)],
                'expiry_date': past_date,
            })

    def test_16_action_update_status_and_send_pending_reminders(self):
        """Test action_update_status validation/execution and _send_pending_reminders."""
        req = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'state': 'sent',
        })
        with self.assertRaises(UserError):
            req.action_update_status()

        self.env['docusign.lines'].create({
            'request_id': req.id,
            'partner_id': self.partner_1.id,
            'document': 'Contract.pdf',
            'envelope_id': 'ENV-UPD-01',
            'status': 'sent',
        })
        with patch.object(type(req), '_sync_document_status') as mock_sync:
            res = req.action_update_status()
            mock_sync.assert_called_once()
            self.assertEqual(res.get('type'), 'ir.actions.client')

        sent_partners = req._send_pending_reminders()
        self.assertIn(self.partner_1, sent_partners)
        self.assertTrue(req.reminder_sent)

    def test_17_action_download_document(self):
        """Test action_download_document calls action_update_status."""
        req = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'credentials_id': self.credential.id,
            'state': 'sent',
        })
        self.env['docusign.lines'].create({
            'request_id': req.id,
            'partner_id': self.partner_1.id,
            'document': 'Contract.pdf',
            'envelope_id': 'ENV-DL-01',
            'status': 'sent',
        })
        with patch.object(type(req), 'action_update_status') as mock_update:
            req.action_download_document()
            mock_update.assert_called_once()

    def test_18_document_assignments_validation_errors(self):
        """Test _get_document_assignments validation errors across mandatory and custom modes."""
        # 1. Custom mode with no custom lines
        req_custom = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'selection_type': 'custom',
            'partner_ids': [Command.link(self.partner_1.id)],
        })
        with self.assertRaises(UserError) as cm:
            req_custom._get_document_assignments()
        self.assertIn("custom document assignment lines", str(cm.exception))

        # 2. Custom line with no documents assigned
        req_custom.custom_line_ids = [(0, 0, {
            'partner_id': self.partner_1.id,
            'document_ids': False,
        })]
        with self.assertRaises(UserError) as cm:
            req_custom._get_document_assignments()
        self.assertIn("Please assign at least one document", str(cm.exception))

        # 3. Customer with no email configured
        partner_no_email = self.env['res.partner'].create({'name': 'Recipient Without Email'})
        req_mandatory = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'selection_type': 'mandatory',
            'partner_ids': [Command.link(partner_no_email.id)],
            'document_ids': [Command.link(self.doc_attachment.id)],
        })
        with self.assertRaises(UserError) as cm:
            req_mandatory._get_document_assignments()
        self.assertIn("does not have an email address configured", str(cm.exception))

    def test_19_action_open_document_wizard_validations(self):
        """Test action_open_document_wizard error conditions."""
        req_empty = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
        })
        # No documents to configure
        with self.assertRaises(UserError) as cm:
            req_empty.action_open_document_wizard()
        self.assertIn("No document found to configure fields", str(cm.exception))

        # Non-existent attachment ID
        with self.assertRaises(UserError) as cm:
            req_empty.action_open_document_wizard(attachment_ids=9999999)
        self.assertIn("does not exist", str(cm.exception))

    def test_20_action_send_document_validations(self):
        """Test action_send_document error conditions when missing credentials or documents."""
        # 1. Missing credentials
        req_no_cred = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'partner_ids': [Command.link(self.partner_1.id)],
            'document_ids': [Command.link(self.doc_attachment.id)],
            'credentials_id': False,
            'state': 'draft',
        })
        with patch.object(type(req_no_cred), '_get_default_credentials', return_value=self.env['docusign.credentials']):
            with self.assertRaises(UserError) as cm:
                req_no_cred.action_send_document()
            self.assertIn("has no active DocuSign credentials", str(cm.exception))

        # 2. Mandatory mode with no documents selected
        req_no_docs = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'credentials_id': self.credential.id,
            'selection_type': 'mandatory',
            'partner_ids': [Command.link(self.partner_1.id)],
            'document_ids': False,
            'state': 'draft',
        })
        with self.assertRaises(UserError) as cm:
            req_no_docs.action_send_document()
        self.assertIn("Please select at least one document", str(cm.exception))

        # 3. Custom mode with no custom documents assigned
        req_custom_no_docs = self.env['docusign.document.request'].create({
            'company_id': self.env.company.id,
            'credentials_id': self.credential.id,
            'selection_type': 'custom',
            'partner_ids': [Command.link(self.partner_1.id)],
            'custom_line_ids': [(0, 0, {
                'partner_id': self.partner_1.id,
                'document_ids': False,
            })],
            'state': 'draft',
        })
        with self.assertRaises(UserError) as cm:
            req_custom_no_docs.action_send_document()
        self.assertIn("Please upload and assign at least one document", str(cm.exception))
