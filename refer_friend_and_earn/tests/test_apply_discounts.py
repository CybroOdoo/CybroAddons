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
from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestApplyDiscounts(TransactionCase):
    """Test suite for apply.discounts model and its constraint functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.discount_rule = cls.env['apply.discounts'].create({
            'starting_points': 10,
            'end_points': 50,
            'discount': 5.0,
        })

    def test__check_points_range(self):
        """Test _check_points_range constraint for starting and end points."""
        # 1. Valid range on creation: starting_points < end_points
        valid_rule = self.env['apply.discounts'].create({
            'starting_points': 60,
            'end_points': 100,
            'discount': 10.0,
        })
        self.assertEqual(valid_rule.starting_points, 60)
        self.assertEqual(valid_rule.end_points, 100)
        self.assertEqual(valid_rule.discount, 10.0)

        # 2. Boundary condition: starting_points == end_points (valid)
        equal_rule = self.env['apply.discounts'].create({
            'starting_points': 150,
            'end_points': 150,
            'discount': 15.0,
        })
        self.assertEqual(equal_rule.starting_points, 150)
        self.assertEqual(equal_rule.end_points, 150)

        # 3. Invalid range on creation: starting_points > end_points
        with self.assertRaises(ValidationError):
            self.env['apply.discounts'].create({
                'starting_points': 120,
                'end_points': 80,
                'discount': 20.0,
            })

        # 4. Invalid range on update/write: setting starting_points > end_points
        with self.assertRaises(ValidationError):
            self.discount_rule.write({
                'starting_points': 70,
            })

        # 5. Invalid range on update/write: setting end_points < starting_points
        with self.assertRaises(ValidationError):
            self.discount_rule.write({
                'end_points': 5,
            })

    def test_check_points_range(self):
        """Alias test method for check_points_range without leading underscore."""
        self.test__check_points_range()
