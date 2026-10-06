# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.

###############################################################################
from odoo.tests.common import TransactionCase
from odoo import Command

class TestRequisitionOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Vendor',
            'supplier_rank': 1,
        })
        
        cls.product = cls.env['product.product'].create({
            'name': 'Test Requisition Product',
            'type': 'consu',
            'seller_ids': [Command.create({
                'partner_id': cls.partner.id,
                'min_qty': 1.0,
                'price': 10.0,
            })]
        })

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
        })

        cls.requisition = cls.env['employee.purchase.requisition'].create({
            'employee_id': cls.employee.id,
            'user_id': cls.env.user.id,
            'requisition_order_ids': [Command.create({
                'product_id': cls.product.id,
                'quantity': 5,
                'requisition_type': 'purchase_order',
            })]
        })

        cls.order_line = cls.requisition.requisition_order_ids[0]

    def test_compute_product_id(self):
        """Test if the product description is computed correctly."""
        self.order_line._compute_product_id()
        self.assertEqual(self.order_line.description, self.product.name, "Description should match product name")

    def test_compute_requisition_type(self):
        """Test fetching of product vendors."""
        self.order_line._compute_requisition_type()
        self.assertIn(self.partner.id, self.order_line.partner_ids.ids, "Partner should be in partner_ids")
