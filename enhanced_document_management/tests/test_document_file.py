# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

"""Tests for the document.file model."""

from odoo.tests import TransactionCase

class TestDocumentFileModel(TransactionCase):
    def setUp(self):
        super().setUp()
        # partner, user, workspace, tag for relations
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'partner_id': self.partner.id,
        })
        self.workspace = self.env['document.workspace'].create({
            'name': 'Test Workspace',
        })

        self.tag = self.env['document.tag'].create({'name': 'Test Tag'})

    def test_create_document_file(self):
        doc = self.env['document.file'].create({
            'name': 'test.txt',
            'attachment': b'ZGF0YQ==',
            'workspace_id': self.workspace.id,
            'user_id': self.user.id,
            'document_tag_ids': [(6, 0, [self.tag.id])],
        })
        self.assertTrue(doc.id)
        self.assertEqual(doc.document_tag_ids, self.tag)
        self.assertEqual(doc.user_id, self.user)
