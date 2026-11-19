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
from datetime import date, datetime

from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged('post_install', '-at_install')
class TestSaleOrderWarranty(SaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warranty_product = cls.env['product.product'].create({
            'name': 'Warranty Product',
            'list_price': 120.0,
            'is_warranty_available': True,
            'warranty_duration': 12,
        })
        cls.other_product = cls.env['product.product'].create({
            'name': 'Non Warranty Product',
            'list_price': 80.0,
        })

    def test_confirm_sets_warranty_flag(self):
        order = self._create_so(order_line=[
            Command.create({'product_id': self.other_product.id}),
            Command.create({'product_id': self.warranty_product.id}),
        ])
        plain_order = self._create_so(order_line=[
            Command.create({'product_id': self.other_product.id}),
        ])

        (order | plain_order).action_confirm()

        self.assertTrue(order.is_warranty_check)
        self.assertFalse(plain_order.is_warranty_check)

    def test_warranty_expiry_date_on_line(self):
        order = self._create_so(order_line=[
            Command.create({'product_id': self.warranty_product.id}),
            Command.create({'product_id': self.other_product.id}),
        ])
        order.date_order = datetime(2026, 3, 10, 9, 0)

        warranty_line, other_line = order.order_line
        self.assertEqual(warranty_line.warranty_expiry_date, date(2027, 3, 10))
        self.assertFalse(other_line.warranty_expiry_date)

        # A later change of the product's duration keeps the sold warranty.
        self.warranty_product.sudo().warranty_duration = 24
        self.assertEqual(warranty_line.warranty_expiry_date, date(2027, 3, 10))

    def test_action_open_warranty_details(self):
        order = self._create_so(order_line=[
            Command.create({'product_id': self.warranty_product.id}),
            Command.create({'product_id': self.other_product.id}),
        ])

        action = order.action_open_warranty_details()

        self.assertEqual(action['res_model'], 'sale.order.line')
        lines = self.env['sale.order.line'].sudo().search(action['domain'])
        self.assertEqual(lines.product_id, self.warranty_product)

    def test_warranty_duration_must_be_positive(self):
        template = self.warranty_product.product_tmpl_id.sudo()
        with self.assertRaises(ValidationError):
            template.warranty_duration = -5
        with self.assertRaises(ValidationError):
            template.warranty_duration = 0

        # Products without a warranty may keep a zero duration.
        self.other_product.product_tmpl_id.sudo().warranty_duration = 0
        self.assertFalse(self.other_product.is_warranty_available)
