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
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDocuSignLines(TransactionCase):
    """Unit tests for docusign.lines model in models/docusign_lines.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Line Test Partner',
            'email': 'partner@example.com',
        })
        cls.doc_request = cls.env['docusign.document.request'].create({
            'name': 'REQ/TEST/001',
            'partner_ids': [(4, cls.partner.id)],
            'company_id': cls.env.company.id,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def test_01_display_name_computation(self):
        """Test _compute_display_name logic under various field combinations."""
        # 1. request_id and document
        line1 = self.env['docusign.lines'].create({
            'request_id': self.doc_request.id,
            'document': 'Contract.pdf',
        })
        self.assertEqual(line1.display_name, f"{self.doc_request.name} - Contract.pdf")

        # 2. request_id only
        line2 = self.env['docusign.lines'].create({
            'request_id': self.doc_request.id,
        })
        self.assertEqual(line2.display_name, self.doc_request.name)

        # 3. document only
        line3 = self.env['docusign.lines'].create({
            'document': 'Agreement.pdf',
        })
        self.assertEqual(line3.display_name, 'Agreement.pdf')

        # 4. envelope_id only
        line4 = self.env['docusign.lines'].create({
            'envelope_id': 'ENV-98765',
        })
        self.assertEqual(line4.display_name, 'ENV-98765')

        # 5. Empty
        line5 = self.env['docusign.lines'].create({})
        self.assertEqual(line5.display_name, 'Document')

    def test_02_process_webhook_no_lines_found(self):
        """Test _process_docusign_webhook when no lines match the envelope ID."""
        # Should gracefully return without error
        self.env['docusign.lines']._process_docusign_webhook('non-existent-envelope', 'completed')

    def test_03_process_webhook_document_request(self):
        """Test _process_docusign_webhook triggers sync on associated document request."""
        self.env['docusign.lines'].create({
            'request_id': self.doc_request.id,
            'envelope_id': 'ENV-REQ-101',
            'status': 'sent',
        })

        with patch.object(type(self.env['docusign.document.request']), '_sync_document_status') as mock_sync:
            self.env['docusign.lines']._process_docusign_webhook('ENV-REQ-101', 'completed')
            mock_sync.assert_called_once_with(target_envelope_id='ENV-REQ-101')

    def test_04_process_webhook_sale_order(self):
        """Test _process_docusign_webhook triggers download on associated sale order."""
        self.env['docusign.lines'].create({
            'docusign_id': self.sale_order.id,
            'envelope_id': 'ENV-SO-202',
            'status': 'sent',
        })

        with patch.object(type(self.env['sale.order']), 'action_download_document') as mock_download:
            self.env['docusign.lines']._process_docusign_webhook('ENV-SO-202', 'completed')
            mock_download.assert_called_once()

    def test_05_process_webhook_sale_order_exception_handling(self):
        """Test _process_docusign_webhook catches and logs exceptions from sale.order download without failing."""
        self.env['docusign.lines'].create({
            'docusign_id': self.sale_order.id,
            'envelope_id': 'ENV-SO-ERR',
            'status': 'sent',
        })
        with patch.object(type(self.env['sale.order']), 'action_download_document', side_effect=Exception("Simulated error")):
            # Should not raise exception
            self.env['docusign.lines']._process_docusign_webhook('ENV-SO-ERR', 'completed')
