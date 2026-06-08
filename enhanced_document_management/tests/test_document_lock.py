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

"""Tests for the document.lock model."""

from odoo.tests import TransactionCase

class TestDocumentLockModel(TransactionCase):
    def setUp(self):
        super().setUp()
        # create partner, user, workspace, document
        self.partner = self.env['res.partner'].create({'name': 'Partner'})
        self.user = self.env['res.users'].create({
            'name': 'User',
            'login': 'lock_user',
            'partner_id': self.partner.id,
        })
        self.workspace = self.env['document.workspace'].create({
            'name': 'Workspace',
        })
        self.doc = self.env['document.file'].create({
            'name': 'file.txt',
            'attachment': b'ZGF0YQ==',
            'workspace_id': self.workspace.id,
            'user_id': self.user.id,
        })

    def test_create_lock(self):
        lock = self.env['document.lock'].create({
            'document_file_id': self.doc.id,
            'password': 'secret_password',
        })
        self.assertEqual(lock.document_file_id, self.doc)
        self.assertEqual(lock.password, 'secret_password')
