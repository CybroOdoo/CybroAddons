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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosOrderLine(TransactionCase):
    """Test cases for models/pos_order_line.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'POS Order Line Test Config',
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.env.uid,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Order Line Question Product',
            'available_in_pos': True,
            'sale_ok': True,
            'list_price': 10.0,
            'taxes_id': [(5, 0)],
        })

    def test_question_list_field_on_order_line(self):
        """question_list stores and updates text values on pos.order.line."""
        order = self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'session_id': self.pos_session.id,
            'amount_tax': 0.0,
            'amount_total': 20.0,
            'amount_paid': 20.0,
            'amount_return': 0.0,
            'lines': [
                (0, 0, {
                    'name': 'OL/0001',
                    'product_id': self.product.id,
                    'price_unit': 10.0,
                    'qty': 1.0,
                    'tax_ids': False,
                    'price_subtotal': 10.0,
                    'price_subtotal_incl': 10.0,
                    'question_list': 'Extra cheese, No onions',
                }),
                (0, 0, {
                    'name': 'OL/0002',
                    'product_id': self.product.id,
                    'price_unit': 10.0,
                    'qty': 1.0,
                    'tax_ids': False,
                    'price_subtotal': 10.0,
                    'price_subtotal_incl': 10.0,
                }),
            ],
        })

        self.assertEqual(order.lines[0].question_list, 'Extra cheese, No onions')
        self.assertFalse(order.lines[1].question_list)

        order.lines[1].write({'question_list': 'Well done'})
        self.assertEqual(order.lines[1].question_list, 'Well done')

    def test_load_pos_data_fields_includes_question_list(self):
        """_load_pos_data_fields on pos.order.line includes question_list and base fields."""
        fields_list = self.env['pos.order.line']._load_pos_data_fields(self.pos_config)
        self.assertIn('question_list', fields_list)
        self.assertIn('id', fields_list)
        self.assertIn('product_id', fields_list)
        self.assertIn('qty', fields_list)
