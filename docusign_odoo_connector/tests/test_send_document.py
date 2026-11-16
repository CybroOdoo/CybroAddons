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
import json
from unittest.mock import MagicMock, patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSendDocumentWizard(TransactionCase):
    """Unit tests for send.document wizard in wizard/send_document.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Wizard Partner',
            'email': 'wizard.partner@example.com',
        })
        cls.att_key = cls.env['ir.attachment'].create({
            'name': 'wiz_key.pem',
            'type': 'binary',
            'raw': b"-----BEGIN RSA PRIVATE KEY-----\nMOCK\n-----END RSA PRIVATE KEY-----",
        })
        cls.credential = cls.env['docusign.credentials'].create({
            'name': 'Wizard Credential',
            'integrator_key': 'int-key-wiz',
            'account_id_data': 'acc-id-wiz',
            'user_id_data': 'user-id-wiz',
            'private_key_ids': [Command.link(cls.att_key.id)],
            'company_id': cls.env.company.id,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'credentials_id': cls.credential.id,
        })
        cls.pdf_attachment = cls.env['ir.attachment'].create({
            'name': 'sample.pdf',
            'type': 'binary',
            'raw': b"%PDF-1.4 sample content",
        })

    def test_01_onchange_check(self):
        """Test _onchange_check updates check field based on file presence."""
        wiz = self.env['send.document'].new({'reference': 'Test Doc'})
        wiz.file = base64.b64encode(b"Dummy Content").decode('ascii')
        wiz._onchange_check()
        self.assertTrue(wiz.check)

        wiz.file = False
        wiz._onchange_check()
        self.assertFalse(wiz.check)

    def test_02_action_edit_documents(self):
        """Test action_edit_documents behavior with and without file."""
        wiz_no_file = self.env['send.document'].create({
            'reference': 'No File Doc',
            'file': False,
        })
        with self.assertRaises(UserError) as cm:
            wiz_no_file.action_edit_documents()
        self.assertIn('No attachments are added', str(cm.exception))

        wiz_with_file = self.env['send.document'].create({
            'reference': 'With File Doc',
            'file': base64.b64encode(b"dummy").decode('ascii'),
        })
        with self.assertRaises(UserError) as cm:
            wiz_with_file.action_edit_documents()
        self.assertIn('Preview', str(cm.exception))

    def test_03_get_json_data(self):
        """Test get_json_data serializes and sets json tabs on wizard."""
        wiz = self.env['send.document'].create({
            'reference': 'Json Test',
        })
        tabs = [{'signHereTabs': [{'x': 100, 'y': 200}]}]
        wiz.get_json_data(tabs, wiz.id)
        self.assertEqual(wiz.data, json.dumps(tabs))

    def test_04_action_save_document_fields_single(self):
        """Test action_save_document_fields writes tabs to attachment."""
        tabs_json = json.dumps([{'signHere': 'test'}])
        wiz = self.env['send.document'].create({
            'reference': 'Single Att',
            'attachment_id': self.pdf_attachment.id,
            'data': tabs_json,
        })
        res = wiz.action_save_document_fields()
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('tag'), 'display_notification')
        self.assertEqual(self.pdf_attachment.docusign_tabs, tabs_json)

    def test_05_action_save_document_fields_multi_remaining(self):
        """Test action_save_document_fields advances to next attachment when remaining."""
        next_att = self.env['ir.attachment'].create({
            'name': 'next_document.pdf',
            'type': 'binary',
            'raw': b"%PDF-1.4 next doc",
        })
        doc_request = self.env['docusign.document.request'].create({
            'name': 'REQ-WIZ-01',
            'partner_ids': [(4, self.partner.id)],
            'company_id': self.env.company.id,
        })
        wiz = self.env['send.document'].create({
            'reference': 'Multi Att Wizard',
            'document_request_id': doc_request.id,
            'attachment_id': self.pdf_attachment.id,
            'remaining_attachment_ids': json.dumps([next_att.id]),
            'data': json.dumps([{'recipient': 'Partner'}]),
        })
        res = wiz.action_save_document_fields()
        self.assertEqual(res.get('type'), 'ir.actions.act_window')
        self.assertEqual(res.get('res_model'), 'send.document')

    def test_06_action_send_documents_validation(self):
        """Test action_send_documents raises errors when fields are missing."""
        # 1. No data
        wiz_no_data = self.env['send.document'].create({
            'reference': 'No Data',
            'email_id': self.partner.id,
            'res_id': self.sale_order.id,
        })
        with self.assertRaises(UserError) as cm:
            wiz_no_data.action_send_documents()
        self.assertIn('You need to add fields in the document', str(cm.exception))

        # 2. No email on partner
        partner_no_email = self.env['res.partner'].create({'name': 'No Email User'})
        wiz_no_email = self.env['send.document'].create({
            'reference': 'No Email',
            'email_id': partner_no_email.id,
            'res_id': self.sale_order.id,
            'data': json.dumps([{'field': 'tab'}]),
        })
        with self.assertRaises(UserError) as cm:
            wiz_no_email.action_send_documents()
        self.assertIn('Please add recipients email address', str(cm.exception))

        # 3. No credentials setup
        so_no_cred = self.env['sale.order'].create({'partner_id': self.partner.id})
        wiz_no_cred = self.env['send.document'].create({
            'reference': 'No Cred',
            'email_id': self.partner.id,
            'res_id': so_no_cred.id,
            'data': json.dumps([{'field': 'tab'}]),
        })
        with patch.object(type(self.env['docusign.credentials']), 'search', return_value=self.env['docusign.credentials']):
            with self.assertRaises(UserError) as cm:
                wiz_no_cred.action_send_documents()
            self.assertIn('You need to setup docusign credentials', str(cm.exception))

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.action_send_docusign_file')
    def test_07_action_send_documents_success(self, mock_send_file):
        """Test action_send_documents successfully sends document and updates sale.order."""
        mock_response = MagicMock()
        mock_response.status = 'sent'
        mock_response.envelope_id = 'ENV-WIZ-999'
        mock_send_file.return_value = mock_response

        wiz = self.env['send.document'].create({
            'reference': 'Contract Final.pdf',
            'email_id': self.partner.id,
            'res_id': self.sale_order.id,
            'file': base64.b64encode(b"%PDF-1.4 test").decode('ascii'),
            'data': json.dumps([{'signHere': 'tab'}]),
        })

        wiz.action_send_documents()

        mock_send_file.assert_called_once()
        self.assertEqual(len(self.sale_order.docusign_line_ids), 1)
        line = self.sale_order.docusign_line_ids[0]
        self.assertEqual(line.document, 'Contract Final.pdf')
        self.assertEqual(line.status, 'sent')
        self.assertEqual(line.envelope_id, 'ENV-WIZ-999')
        self.assertEqual(line.partner_id, self.partner)
