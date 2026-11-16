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

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResPartnerDocuSign(TransactionCase):
    """Unit tests for res.partner DocuSign features in models/res_partner.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'DocuSign Partner Test',
            'email': 'docusign.partner@example.com',
        })

    def test_01_signed_document_count_and_lines(self):
        """Test signed_document_count compute method and signed_docusign_line_ids relation."""
        # Initial count should be 0
        self.partner._compute_signed_document_count()
        self.assertEqual(self.partner.signed_document_count, 0)
        self.assertEqual(len(self.partner.signed_docusign_line_ids), 0)

        # Create an incomplete / pending document line
        self.env['docusign.lines'].create({
            'partner_id': self.partner.id,
            'document': 'Pending.pdf',
            'status': 'sent',
            'envelope_id': 'ENV-001',
        })
        self.partner._compute_signed_document_count()
        self.assertEqual(self.partner.signed_document_count, 0)
        self.assertEqual(len(self.partner.docusign_line_ids), 1)
        self.assertEqual(len(self.partner.signed_docusign_line_ids), 0)

        # Create a completed document line
        line2 = self.env['docusign.lines'].create({
            'partner_id': self.partner.id,
            'document': 'Signed.pdf',
            'status': 'completed',
            'signed_document': base64.b64encode(b'MockBinary').decode('ascii'),
            'envelope_id': 'ENV-002',
        })
        self.partner.invalidate_recordset(['signed_document_count', 'signed_docusign_line_ids'])
        self.partner._compute_signed_document_count()
        self.assertEqual(self.partner.signed_document_count, 1)
        self.assertIn(line2, self.partner.signed_docusign_line_ids)

        # Create a line with status != completed but signed_document present
        self.env['docusign.lines'].create({
            'partner_id': self.partner.id,
            'document': 'SignedOtherStatus.pdf',
            'status': 'delivered',
            'signed_document': base64.b64encode(b'MockBinary2').decode('ascii'),
            'envelope_id': 'ENV-003',
        })
        self.partner.invalidate_recordset(['signed_document_count', 'signed_docusign_line_ids'])
        self.partner._compute_signed_document_count()
        self.assertEqual(self.partner.signed_document_count, 2)

    def test_02_action_view_signed_documents(self):
        """Test action_view_signed_documents smart button action."""
        action = self.partner.action_view_signed_documents()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'docusign.lines')
        self.assertEqual(action.get('view_mode'), 'list,form')
        self.assertIn(('partner_id', '=', self.partner.id), action.get('domain', []))
        self.assertEqual(action.get('context', {}).get('default_partner_id'), self.partner.id)
