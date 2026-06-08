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

"""Tests for the document.template.request model (wizard)."""

from odoo.tests import TransactionCase

class TestDocumentTemplateRequest(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Partner'})
        self.user = self.env['res.users'].create({
            'name': 'User',
            'login': 'user_test_wizard',
            'partner_id': self.partner.id,
        })
        self.template_doc = self.env['document.request.template'].create({
            'name': 'Sample Template',
            'manager_id': self.user.id,
        })

    def test_create_template_request(self):
        tmpl_req = self.env['document.template.request'].create({
            'name': 'Wizard Test',
            'document_id': self.template_doc.id,
            'template': '<p>Sample</p>',
        })
        self.assertTrue(tmpl_req.id)
        self.assertEqual(tmpl_req.document_id, self.template_doc)
