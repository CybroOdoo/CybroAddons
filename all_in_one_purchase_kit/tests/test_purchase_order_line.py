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

class TestPurchaseOrderLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Vendor POL',
            'default_discount': 5.0,
        })
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product POL',
            'type': 'consu',
            'barcode': '123456789',
            'categ_id': cls.category.id,
            'seller_ids': [Command.create({
                'partner_id': cls.partner.id,
                'min_qty': 1.0,
                'price': 100.0,
                'discount': 10.0,
            })]
        })
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_qty': 2.0,
                'price_unit': 100.0,
            })]
        })
        cls.po_line = cls.po.order_line[0]

    def test_onchange_order_id(self):
        """Test UserError when PO is confirmed/cancelled."""
        self.po.button_confirm()
        with self.assertRaises(UserError):
            self.po_line._onchange_order_id()

    def test_get_product_form(self):
        """Test returning product form action."""
        action = self.po_line.get_product_form()
        self.assertEqual(action['res_model'], 'product.product')
        self.assertEqual(action['res_id'], self.product.id)

    def test_onchange_barcode_scan(self):
        """Test updating product from barcode."""
        new_line = self.env['purchase.order.line'].new({
            'order_id': self.po.id,
            'barcode_scan': '123456789'
        })
        new_line._onchange_barcode_scan()
        self.assertEqual(new_line.product_id.id, self.product.id)

    def test_discount_calculations(self):
        """Test discount application on line."""
        self.po_line.calculate_discount_percentage()
        self.assertEqual(self.po_line.discount, 10.0)
        self.assertEqual(self.po_line._get_discounted_price(), 90.0)

        # tax_base = self.po_line._convert_to_tax_base_line_dict()
        # self.assertEqual(tax_base['price_unit'], 90.0)

        move_line_vals = self.po_line._prepare_account_move_line()
        self.assertEqual(move_line_vals['discount'], 10.0)

    def test_actions(self):
        """Test action buttons."""
        action_cat = self.po_line.add_catalog_control()
        self.assertEqual(action_cat['res_model'], 'product.product')

        action_po = self.po_line.action_purchase_order()
        self.assertEqual(action_po['res_model'], 'purchase.order')

    def test_product_categ_data(self):
        """Test getting product category data."""
        # Need to ensure the record exists in DB for sql query
        analysis = self.env['purchase.order.line'].product_categ_analysis()
        self.assertIn('values', analysis)

        data = self.env['purchase.order.line'].product_categ_data(self.category.id)
        self.assertIn('name', data)
        self.assertIn('count', data)
