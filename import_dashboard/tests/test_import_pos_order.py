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
class TestImportPosOrder(TransactionCase):

    def setUp(self):
        super().setUp()
        if 'pos.order' not in self.env or 'pos.session' not in self.env:
            self.skipTest("Point of Sale app is not installed")
        self.Wizard = self.env['import.pos.order']
        self.Partner = self.env['res.partner'].create({'name': 'POS Customer Test'})
        self.Product = self.env['product.product'].create({
            'name': 'POS Test Product',
            'available_in_pos': True if 'available_in_pos' in self.env['product.product']._fields else False,
            'lst_price': 10.0,
        })

    def _get_session(self):
        """Return an open POS session, opening one if needed"""
        session = self.env['pos.session'].search([('state', '=', 'opened')], limit=1)
        if not session:
            pos_config = self.env['pos.config'].search([], limit=1)
            if pos_config:
                session = self.env['pos.session'].create({
                    'config_id': pos_config.id,
                    'user_id': self.env.user.id,
                })
        if not session:
            self.skipTest("No POS configuration found to open a session")
        return session

    def test_action_import_pos_order_csv(self):
        """Test importing POS order from CSV"""
        session = self._get_session()

        csv_content = (
            "Order Ref,Receipt Number,Order Date,Session,Customer,Responsible,Product,Quantity,Unit Price,Discount %,Sub Total,Total,Paid Amount,Amount Returned\n"
            f"POS/TEST/001,REC-001,2026-06-01 10:00:00,{session.name},POS Customer Test,{self.env.user.name},POS Test Product,2,10.0,0,20.0,20.0,20.0,0.0"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'import_product_by': 'name'
        })
        wizard.action_import_pos_order()

        order = self.env['pos.order'].search([('name', '=', 'POS/TEST/001')])
        self.assertTrue(order, "POS Order should be created")

    def test_import_pos_order_by_barcode(self):
        """Products are matched by barcode when Match Products By is Barcode"""
        session = self._get_session()
        self.Product.barcode = 'POSTEST0001'
        csv_content = (
            "Order Ref,Session,Customer,Product,Barcode,Quantity,Unit Price,Sub Total\n"
            f"POS/TEST/002,{session.name},POS Customer Test,Name In File,POSTEST0001,1,10.0,10.0"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'import_product_by': 'barcode',
        })
        wizard.action_import_pos_order()

        order = self.env['pos.order'].search([('name', '=', 'POS/TEST/002')])
        self.assertEqual(order.lines.product_id, self.Product)

    def test_import_pos_order_without_product(self):
        """A row with no product creates the order without an empty line"""
        session = self._get_session()
        csv_content = (
            "Order Ref,Session,Customer,Quantity,Unit Price,Sub Total\n"
            f"POS/TEST/003,{session.name},POS Customer Test,1,10.0,10.0"
        )
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8')).decode('utf-8'),
            'import_product_by': 'name',
        })
        wizard.action_import_pos_order()

        order = self.env['pos.order'].search([('name', '=', 'POS/TEST/003')])
        self.assertTrue(order, "POS Order should be created")
        self.assertFalse(order.lines, "No empty order line should be created")
