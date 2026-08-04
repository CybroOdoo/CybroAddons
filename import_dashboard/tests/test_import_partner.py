# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
from odoo.tests.common import TransactionCase

class TestImportPartner(TransactionCase):

    def setUp(self):
        super(TestImportPartner, self).setUp()
        self.Wizard = self.env['import.partner']

    def test_action_import_partner_csv(self):
        """Test importing partner from CSV"""
        csv_content = "Name,Email,Phone\nTest Partner,test@example.com,123456"
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8'))
        })
        
        if hasattr(wizard, 'action_import_partner'):
            wizard.action_import_partner()
        
        partner = self.env['res.partner'].search([('name', '=', 'Test Partner')])
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.email, 'test@example.com')
