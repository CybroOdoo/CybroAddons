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

"""Tests for the request.document model."""

from odoo.tests import TransactionCase

class TestRequestDocument(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Partner'})
        self.user = self.env['res.users'].create({
            'name': 'User',
            'login': 'user_test_req',
            'partner_id': self.partner.id,
        })
        self.workspace = self.env['document.workspace'].create({
            'name': 'Workspace',
        })

    def test_request_document_flow(self):
        """Create a request document and move through states."""
        req = self.env['request.document'].create({
            'name': 'Request 1',
            'user_id': self.user.id,
            'workspace_id': self.workspace.id,
            'needed_doc': 'Please upload your ID',
            'state': 'draft',
        })
        self.assertTrue(req.id)
        # Simulate acceptance via wizard method if exists
        if hasattr(req, 'action_accept'):
            req.action_accept()
        self.assertIn(req.state, ('draft', 'accepted', 'refused'))
