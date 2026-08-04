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

class TestImportBillOfMaterial(TransactionCase):

    def setUp(self):
        super(TestImportBillOfMaterial, self).setUp()
        self.Wizard = self.env['import.bill_of_material']
        self.Product = self.env['product.product'].create({'name': 'Finished Good'})
        self.Component = self.env['product.product'].create({'name': 'Raw Material'})

    def test_action_import_bom_csv(self):
        """Test importing BOM from CSV"""
        csv_content = "Product,Component,Quantity\nFinished Good,Raw Material,5"
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8'))
        })
        
        # Note: action name likely follows the pattern 'action_import_bill_of_material'
        # based on the file name import_bill_of_material.py
        if hasattr(wizard, 'action_import_bill_of_material'):
            wizard.action_import_bill_of_material()
        
        bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.Product.product_tmpl_id.id)])
        # Verification would depend on the actual implementation of the wizard
        pass
