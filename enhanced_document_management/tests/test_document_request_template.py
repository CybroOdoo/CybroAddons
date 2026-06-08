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

"""Tests for the document.request.template model.
"""

from odoo.tests import TransactionCase

class TestDocumentRequestTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create partner and user
        self.partner = self.env['res.partner'].create({'name': 'Partner'})
        self.user = self.env['res.users'].create({
            'name': 'User',
            'login': 'user_test',
            'partner_id': self.partner.id,
        })
        # Create a tag for many2many
        self.tag = self.env['document.tag'].create({'name': 'Tag'})

    def test_create_request_template(self):
        tmpl = self.env['document.request.template'].create({
            'name': 'Template Test',
            'manager_id': self.user.id,
        })
        self.assertEqual(tmpl.manager_id, self.user)
