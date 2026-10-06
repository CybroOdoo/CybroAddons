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
from odoo.exceptions import UserError
from odoo import Command

class TestProductProduct(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({'name': 'Test PP Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test PP',
            'type': 'consu',
        })
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_qty': 10.0,
                'price_unit': 50.0,
            })]
        })
        cls.po.button_confirm()

    def test_action_purchase_product_prices(self):
        """Test returning purchase history"""
        self.product.order_partner_id = self.partner.id
        action = self.product.action_purchase_product_prices()
        self.assertEqual(action['res_model'], 'purchase.order.line')
        self.assertIn(self.po.order_line[0].id, action['domain'][0][2])

        # Test error when no history
        new_prod = self.env['product.product'].create({'name': 'New'})
        with self.assertRaises(UserError):
            new_prod.action_purchase_product_prices()

    def test_most_purchased_product(self):
        """Test most purchased product method"""
        data = self.env['product.product'].most_purchased_product()
        self.assertIn('purchased_qty', data)
        self.assertTrue(len(data['purchased_qty']) >= 1)

    def test_add_to_rfq(self):
        """Test adding product to RFQ"""
        po2 = self.env['purchase.order'].create({'partner_id': self.partner.id})
        self.product.with_context(order_id=po2.id).add_to_rfq()
        self.assertEqual(len(po2.order_line), 1)
        self.assertEqual(po2.order_line.product_id.id, self.product.id)
        self.assertEqual(po2.order_line.product_uom_qty, 1.0) # wait, default qty? wait `purchase.order.line.create` does not set qty? Ah, the code sets it to default. If we call it again, it increments.
        
        self.product.with_context(order_id=po2.id).add_to_rfq()
        self.assertEqual(po2.order_line.product_uom_qty, 2.0)
