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

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestIrAttachmentDocuSign(TransactionCase):
    """Unit tests for ir.attachment docusign extension in models/ir_attachment.py."""

    def test_01_docusign_tabs_field_storage(self):
        """Test storing and retrieving docusign_tabs field on ir.attachment."""
        tabs_payload = json.dumps([
            {
                'recipient': 'Test Contact',
                'signHereTabs': [{'xPosition': 100, 'yPosition': 200, 'pageNumber': 1}],
            }
        ])

        attachment = self.env['ir.attachment'].create({
            'name': 'document_with_tabs.pdf',
            'type': 'binary',
            'raw': b"%PDF-1.4 sample content",
            'docusign_tabs': tabs_payload,
        })

        self.assertEqual(attachment.docusign_tabs, tabs_payload)

        # Test updating the tabs
        updated_tabs = json.dumps([{'recipient': 'Updated Contact'}])
        attachment.write({'docusign_tabs': updated_tabs})
        self.assertEqual(attachment.docusign_tabs, updated_tabs)

    def test_02_docusign_tabs_default_empty(self):
        """Test docusign_tabs is False/empty by default."""
        attachment = self.env['ir.attachment'].create({
            'name': 'simple_doc.pdf',
            'type': 'binary',
            'raw': b"%PDF-1.4 simple content",
        })
        self.assertFalse(attachment.docusign_tabs)
