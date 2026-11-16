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
class TestPosOrderReceipt(TransactionCase):
    """Test cases for models/pos_order_receipt.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'POS Receipt Test Config',
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.env.uid,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Receipt Question Product',
            'available_in_pos': True,
            'sale_ok': True,
            'list_price': 10.0,
            'taxes_id': [(5, 0)],
        })

    def _create_order_with_lines(self, line_specs):
        lines_cmd = []
        for idx, spec in enumerate(line_specs, start=1):
            vals = {
                'name': f'OL/{idx:04d}',
                'product_id': self.product.id,
                'price_unit': 10.0,
                'discount': 0.0,
                'qty': 1.0,
                'tax_ids': False,
                'price_subtotal': 10.0,
                'price_subtotal_incl': 10.0,
            }
            if 'question_list' in spec:
                vals['question_list'] = spec['question_list']
            lines_cmd.append((0, 0, vals))

        total = 10.0 * len(line_specs)
        return self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'session_id': self.pos_session.id,
            'lines': lines_cmd,
            'amount_tax': 0.0,
            'amount_total': total,
            'amount_paid': total,
            'amount_return': 0.0,
        })

    def test_order_receipt_generate_line_data_with_and_without_questions(self):
        """_order_receipt_generate_line_data includes question_list or False per line."""
        order = self._create_order_with_lines([
            {'question_list': 'No salt, Extra sauce'},
            {},
            {'question_list': ''},
        ])

        line_data = order._order_receipt_generate_line_data()
        self.assertEqual(len(line_data), 3)
        self.assertEqual(line_data[0]['question_list'], 'No salt, Extra sauce')
        self.assertIs(line_data[1]['question_list'], False)
        self.assertIs(line_data[2]['question_list'], False)

    def test_order_receipt_generate_data_contains_line_questions(self):
        """order_receipt_generate_data exposes question_list in receipt lines."""
        order = self._create_order_with_lines([
            {'question_list': 'Medium rare'},
        ])

        receipt_data = order.order_receipt_generate_data()
        self.assertIn('lines', receipt_data)
        self.assertEqual(len(receipt_data['lines']), 1)
        self.assertEqual(receipt_data['lines'][0]['question_list'], 'Medium rare')

    def test_order_receipt_generate_line_data_empty_order(self):
        """_order_receipt_generate_line_data returns an empty list when order has no lines."""
        order = self._create_order_with_lines([])
        self.assertEqual(order._order_receipt_generate_line_data(), [])
