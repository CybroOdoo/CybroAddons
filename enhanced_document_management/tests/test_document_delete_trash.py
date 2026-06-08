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

"""Tests for the document.delete.trash model."""

from odoo.tests import TransactionCase

class TestDocumentDeleteTrash(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Partner'})
        self.user = self.env['res.users'].create({
            'name': 'User',
            'login': 'delete_trash_user',
            'partner_id': self.partner.id,
        })
        self.workspace = self.env['document.workspace'].create({
            'name': 'Workspace',
        })
        self.doc = self.env['document.file'].create({
            'name': 'test.txt',
            'attachment': b'ZGF0YQ==',
            'workspace_id': self.workspace.id,
            'user_id': self.user.id,
        })

    def test_create_delete_trash(self):
        trash = self.env['document.delete.trash'].create({
            'document_file_id': self.doc.id,
        })
        self.assertTrue(trash.id)
        self.assertEqual(trash.document_file_id, self.doc)
