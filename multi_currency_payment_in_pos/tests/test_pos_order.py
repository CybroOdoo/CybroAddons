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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', 'at_install')
class TestPosOrder(TransactionCase):
    """Test multi-currency receipt data generation on pos.order."""

    def setUp(self):
        super().setUp()
        self.payment_method = self.env['pos.payment.method'].search(
            [('type', '=', 'bank')],
            limit=1,
        )
        if not self.payment_method:
            self.payment_method = self.env['pos.payment.method'].create({
                'name': 'Bank Test Method',
                'type': 'bank',
                'receivable_account_id': self.env['account.account'].search(
                    [('account_type', '=', 'asset_receivable')],
                    limit=1,
                ).id,
            })
        self.pos_config = self.env['pos.config'].create({
            'name': 'POS Order Multi Currency Test',
            'enable_multicurrency': True,
            'payment_method_ids': [(4, self.payment_method.id)],
        })
        self.session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })
        self.pos_order = self.env['pos.order'].create({
            'session_id': self.session.id,
            'lines': [(0, 0, {
                'name': 'Test Line',
                'product_id': self.env['product.product'].create({
                    'name': 'Test Product',
                    'available_in_pos': True,
                    'list_price': 100.0,
                }).id,
                'price_unit': 100.0,
                'qty': 1.0,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
            })],
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
        })

    def test_order_receipt_generate_payment_data_with_multicurrency(self):
        """Test receipt payment data correctly includes multi-currency values."""
        self.env['pos.payment'].create({
            'pos_order_id': self.pos_order.id,
            'payment_method_id': self.payment_method.id,
            'amount': 100.0,
            'payment_currency': 'EUR',
            'currency_amount': 110.0,
        })

        payment_data = self.pos_order._order_receipt_generate_payment_data()
        self.assertTrue(payment_data)
        last_payment = payment_data[-1]
        self.assertEqual(last_payment.get('payment_currency'), 'EUR')
        self.assertEqual(last_payment.get('currency_amount'), '110.00')

    def test_order_receipt_generate_payment_data_without_multicurrency(self):
        """Test receipt payment data handles standard payments without foreign currency values."""
        self.env['pos.payment'].create({
            'pos_order_id': self.pos_order.id,
            'payment_method_id': self.payment_method.id,
            'amount': 100.0,
        })

        payment_data = self.pos_order._order_receipt_generate_payment_data()
        self.assertTrue(payment_data)
        last_payment = payment_data[-1]
        self.assertFalse(last_payment.get('payment_currency'))
        self.assertFalse(last_payment.get('currency_amount'))
