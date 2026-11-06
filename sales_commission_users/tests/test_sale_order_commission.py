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
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderCommission(TransactionCase):
    """Tests for commission calculation when sale orders are confirmed."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Commission customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Commission product',
            'list_price': 100,
            'taxes_id': [Command.clear()],
        })
        cls.other_product = cls.env['product.product'].create({
            'name': 'Other product',
            'list_price': 50,
            'taxes_id': [Command.clear()],
        })

    def _create_commission(self, commission_type, **values):
        return self.env['sales.commission'].create({
            'name': f'Test {commission_type} commission',
            'commission_type': commission_type,
            'sales_person_ids': [Command.set(self.env.user.ids)],
            **values,
        })

    def _confirm_order(self, lines=None, *, quantity=1, discount=0, partner=None,
                       salesperson=None):
        lines = lines or [{
            'product_id': self.product.id,
            'product_uom_qty': quantity,
            'price_unit': 100,
            'discount': discount,
            'tax_ids': [Command.clear()],
        }]
        order = self.env['sale.order'].create({
            'partner_id': (partner or self.partner).id,
            'user_id': (salesperson or self.env.user).id,
            'order_line': [Command.create(line) for line in lines],
        })
        order.action_confirm()
        return order

    def _assert_commission(self, order, commission_type, amount):
        self.assertEqual(len(order.commission_ids), 1)
        commission_line = order.commission_ids
        self.assertEqual(commission_line.sales_person_id, order.user_id)
        self.assertEqual(commission_line.partner_id, order.partner_id)
        self.assertEqual(commission_line.order_ref, order.name)
        self.assertEqual(commission_line.commission_type, commission_type)
        self.assertAlmostEqual(commission_line.commission_amount, amount)

    def test_standard_commission_uses_order_total(self):
        self._create_commission('standard', std_commission_perc=10)
        order = self._confirm_order(quantity=2)
        self._assert_commission(order, 'standard', order.amount_total * 0.10)
        self.assertEqual(order.commission_ids.description, 'Sales Commission - Standard')
        self.assertEqual(order.commission_ids.commission, 'Test standard commission')

    def test_partner_commission_uses_affiliation_rate(self):
        self._create_commission(
            'partner_based',
            affiliated_commission_perc=15,
            non_affiliated_commission_perc=5,
        )
        for affiliated, expected_rate in ((True, 15), (False, 5)):
            with self.subTest(affiliated=affiliated):
                partner = self.env['res.partner'].create({
                    'name': 'Affiliated customer' if affiliated else 'Regular customer',
                    'affiliated': affiliated,
                })
                order = self._confirm_order(partner=partner)
                self._assert_commission(
                    order, 'partner_based', order.amount_total * expected_rate / 100
                )

    def test_product_commission_only_applies_to_matching_order_lines(self):
        self._create_commission(
            'product_based',
            product_based_ids=[Command.create({
                'product_id': self.product.id,
                'commission': 12,
            })],
        )
        order = self._confirm_order(lines=[
            {
                'product_id': self.product.id,
                'product_uom_qty': 3,
                'price_unit': 100,
                'tax_ids': [Command.clear()],
            },
            {
                'product_id': self.other_product.id,
                'product_uom_qty': 1,
                'price_unit': 50,
                'tax_ids': [Command.clear()],
            },
        ])
        # The current product rule is a percentage of each matching product's list price.
        self._assert_commission(order, 'product_based', 12)

    def test_product_rule_without_matching_product_creates_no_line(self):
        self._create_commission(
            'product_based',
            product_based_ids=[Command.create({
                'product_id': self.other_product.id,
                'commission': 12,
            })],
        )
        order = self._confirm_order()
        self.assertFalse(order.commission_ids)

    def test_discount_commission_applies_at_threshold_and_not_below(self):
        self._create_commission(
            'discount_based',
            discount_based_ids=[Command.create({'discount': 10, 'commission': 20})],
        )
        below_threshold = self._confirm_order(discount=9)
        self.assertFalse(below_threshold.commission_ids)
        order = self._confirm_order(discount=10)
        self._assert_commission(order, 'discount_based', order.amount_total * 0.20)

    def test_commission_is_limited_to_assigned_salespeople(self):
        self._create_commission('standard', std_commission_perc=10)
        salesperson = self.env['res.users'].create({
            'name': 'Different salesperson',
            'login': 'different-salesperson-commission-test',
            'group_ids': [Command.set(self.env.ref('base.group_user').ids)],
        })
        order = self._confirm_order(salesperson=salesperson)
        self.assertFalse(order.commission_ids)

    def test_confirming_already_confirmed_order_is_rejected_without_changing_commission(self):
        self._create_commission('standard', std_commission_perc=10)
        order = self._confirm_order()
        with self.assertRaises(UserError):
            order.action_confirm()
        self.assertEqual(len(order.commission_ids), 1)

    def test_zero_rate_does_not_create_commission_line(self):
        self._create_commission('standard', std_commission_perc=0)
        order = self._confirm_order()
        self.assertFalse(order.commission_ids)
