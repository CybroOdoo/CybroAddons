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
import os
import tempfile
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderDocuSign(TransactionCase):
    """Unit tests for sale.order DocuSign integration in models/sale_order.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Sale Order Customer',
            'email': 'so.customer@example.com',
        })
        cls.att_key = cls.env['ir.attachment'].create({
            'name': 'so_key.pem',
            'type': 'binary',
            'raw': b"-----BEGIN RSA PRIVATE KEY-----\nMOCK\n-----END RSA PRIVATE KEY-----",
        })
        cls.credential = cls.env['docusign.credentials'].create({
            'name': 'SO DocuSign Credential',
            'integrator_key': 'int-key-so',
            'account_id_data': 'acc-id-so',
            'user_id_data': 'user-id-so',
            'private_key_ids': [Command.link(cls.att_key.id)],
            'company_id': cls.env.company.id,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'credentials_id': cls.credential.id,
        })

    def test_01_action_send_document(self):
        """Test action_send_document returns window action for send.document wizard."""
        action = self.sale_order.action_send_document()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'send.document')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('context', {}).get('default_res_id'), self.sale_order.id)
        self.assertEqual(action.get('context', {}).get('default_email_id'), self.partner.id)

    def test_02_action_download_document_no_credential(self):
        """Test action_download_document raises UserError if credentials_id is not set."""
        order_no_cred = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'credentials_id': False,
        })
        with self.assertRaises(UserError):
            order_no_cred.action_download_document()

    def test_03_action_download_document_no_envelope_id(self):
        """Test action_download_document raises UserError if no envelope ID is found."""
        self.env['docusign.lines'].create({
            'docusign_id': self.sale_order.id,
            'document': 'TestDoc.pdf',
            'envelope_id': False,
        })
        with self.assertRaises(UserError):
            self.sale_order.action_download_document()

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.download_documents')
    def test_04_action_download_document_success(self, mock_download):
        """Test action_download_document successfully creates attachment and updates line."""
        # Create a temporary file to simulate downloaded document
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, 'DownloadedSignedDoc.pdf')
        with open(temp_file_path, 'wb') as f:
            f.write(b"%PDF-1.4 Mock signed content")

        mock_download.return_value = ('completed', temp_file_path)

        line = self.env['docusign.lines'].create({
            'docusign_id': self.sale_order.id,
            'document': 'SignedDoc.pdf',
            'envelope_id': 'ENV-SO-12345',
            'status': 'sent',
        })

        self.sale_order.action_download_document()

        self.assertEqual(line.status, 'completed')
        self.assertTrue(line.signed_document)

        # Check attachment created on sale.order
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.sale_order.id),
            ('name', '=', 'DownloadedSignedDoc.pdf'),
        ], limit=1)
        self.assertTrue(attachment)

        # Calling again should skip completed lines and de-duplicate
        self.sale_order.action_download_document()
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.sale_order.id),
            ('name', '=', 'DownloadedSignedDoc.pdf'),
        ])
        self.assertEqual(len(attachments), 1)

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.download_documents')
    def test_05_action_download_document_empty_path_updates_status(self, mock_download):
        """Test action_download_document updates line status when path is empty."""
        mock_download.return_value = ('delivered', '')

        line = self.env['docusign.lines'].create({
            'docusign_id': self.sale_order.id,
            'document': 'DeliveredDoc.pdf',
            'envelope_id': 'ENV-DELIV-99',
            'status': 'sent',
        })

        self.sale_order.action_download_document()
        self.assertEqual(line.status, 'delivered')
