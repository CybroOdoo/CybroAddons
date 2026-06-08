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

"""Tests for the document.trash model."""

from odoo.tests import TransactionCase

class TestDocumentTrashModel(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Partner'})
        self.user = self.env['res.users'].create({
            'name': 'User',
            'login': 'trash_user',
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

    def test_create_trash(self):
        trash = self.env['document.trash'].create({
            'name': 'file.txt',
            'attachment': b'ZGF0YQ==',
            'workspace_id': self.workspace.id,
            'user_id': self.user.id,
        })
        self.assertEqual(trash.workspace_id, self.workspace)
        self.assertEqual(trash.user_id, self.user)
