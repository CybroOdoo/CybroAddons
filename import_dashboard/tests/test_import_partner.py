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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################

import base64
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestImportPartner(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Wizard = self.env['import.partner']

    def test_action_import_partner_csv(self):
        """Test importing partner from CSV"""
        csv_content = "Name,Email,Phone\nTest Partner,test@example.com,123456"
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        })

        if hasattr(wizard, 'action_import_partner'):
            wizard.action_import_partner()

        partner = self.env['res.partner'].search([('name', '=', 'Test Partner')])
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.email, 'test@example.com')
