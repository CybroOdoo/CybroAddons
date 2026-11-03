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
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', 'at_install')
class TestPosPayment(TransactionCase):
    """Test multi-currency fields and data loading on pos.payment."""

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
            'name': 'POS Payment Test Config',
            'enable_multicurrency': True,
            'payment_method_ids': [(4, self.payment_method.id)],
        })
        self.session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })
        self.pos_order = self.env['pos.order'].create({
            'session_id': self.session.id,
            'lines': [(0, 0, {
                'name': 'Product Line',
                'product_id': self.env['product.product'].create({
                    'name': 'Payment Test Product',
                    'available_in_pos': True,
                    'list_price': 50.0,
                }).id,
                'price_unit': 50.0,
                'qty': 1.0,
                'price_subtotal': 50.0,
                'price_subtotal_incl': 50.0,
            })],
            'amount_total': 50.0,
            'amount_tax': 0.0,
            'amount_paid': 50.0,
            'amount_return': 0.0,
        })

    def test_pos_payment_multicurrency_fields(self):
        """Test creating pos.payment with multi-currency fields persists correctly."""
        payment = self.env['pos.payment'].create({
            'pos_order_id': self.pos_order.id,
            'payment_method_id': self.payment_method.id,
            'amount': 50.0,
            'payment_currency': 'GBP',
            'currency_amount': 42.50,
        })

        self.assertEqual(payment.payment_currency, 'GBP')
        self.assertAlmostEqual(payment.currency_amount, 42.50)

    def test_load_pos_data_fields_preserves_empty_super(self):
        """Test _load_pos_data_fields returns empty list if super() is empty to load all fields."""
        fields = self.env['pos.payment']._load_pos_data_fields(self.pos_config.id)
        self.assertIsInstance(fields, list)
        self.assertEqual(fields, [])

    def test_load_pos_data_fields_with_super_fields(self):
        """Test _load_pos_data_fields appends multicurrency fields when super() returns a field list."""
        with patch(
            'odoo.addons.point_of_sale.models.pos_load_mixin.PosLoadMixin._load_pos_data_fields',
            return_value=['id', 'amount'],
        ):
            fields = self.env['pos.payment']._load_pos_data_fields(self.pos_config.id)
            self.assertIsInstance(fields, list)
            self.assertIn('payment_currency', fields)
            self.assertIn('currency_amount', fields)
            self.assertIn('id', fields)
            self.assertIn('amount', fields)

