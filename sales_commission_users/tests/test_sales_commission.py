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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSalesCommissionConfiguration(TransactionCase):
    """Tests for commission configuration and percentage constraints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({'name': 'Commission product'})

    def _create_commission(self, **values):
        return self.env['sales.commission'].create({
            'name': 'Commission configuration',
            'commission_type': 'standard',
            **values,
        })

    def test_commission_percentages_accept_zero_and_one_hundred(self):
        commission = self._create_commission(
            std_commission_perc=0,
            affiliated_commission_perc=100,
            non_affiliated_commission_perc=0,
        )
        self.assertEqual(commission.std_commission_perc, 0)
        self.assertEqual(commission.affiliated_commission_perc, 100)

    def test_commission_percentages_reject_values_outside_range(self):
        for field_name, value in (
            ('std_commission_perc', -0.01),
            ('std_commission_perc', 100.01),
            ('affiliated_commission_perc', -1),
            ('non_affiliated_commission_perc', 101),
        ):
            with self.subTest(field=field_name, value=value):
                with self.assertRaises(ValidationError):
                    self._create_commission(**{field_name: value})

    def test_product_rule_percentage_bounds(self):
        rule = self.env['product.based.sales.commission'].create({
            'product_id': self.product.id,
            'commission': 100,
        })
        self.assertEqual(rule.commission, 100)
        for value in (-0.01, 100.01):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    self.env['product.based.sales.commission'].create({
                        'product_id': self.product.id,
                        'commission': value,
                    })

    def test_discount_rule_validates_threshold_and_commission_bounds(self):
        rule = self.env['discount.based.sales.commission'].create({
            'discount': 0,
            'commission': 100,
        })
        self.assertEqual(rule.commission, 100)
        for values in (
            {'discount': -1, 'commission': 10},
            {'discount': 101, 'commission': 10},
            {'discount': 10, 'commission': -1},
            {'discount': 10, 'commission': 101},
        ):
            with self.subTest(values=values):
                with self.assertRaises(ValidationError):
                    self.env['discount.based.sales.commission'].create(values)

    def test_configuration_one2many_commands_create_rules(self):
        commission = self._create_commission(
            commission_type='product_based',
            product_based_ids=[Command.create({
                'product_id': self.product.id,
                'commission': 7,
            })],
            discount_based_ids=[Command.create({
                'discount': 5,
                'commission': 12,
            })],
        )
        self.assertEqual(commission.product_based_ids.product_id, self.product)
        self.assertEqual(commission.discount_based_ids.discount, 5)

