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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Unit tests for the commission.graduated model."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestCommissionGraduated(TransactionCase):
    """Test cases for commission.graduated model functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.commission = cls.env['crm.commission'].create({
            'name': 'Graduated Commission Plan',
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
            'type': 'revenue',
            'revenue_type': 'graduated',
        })

    def test__compute_sequence(self):
        """Test _compute_sequence correctly numbers graduated rules sequentially."""
        rule1 = self.env['commission.graduated'].create({
            'commission_id': self.commission.id,
            'amount_from': 0.0,
            'amount_to': 1000.0,
            'graduated_commission_rate': 5.0,
        })
        rule2 = self.env['commission.graduated'].create({
            'commission_id': self.commission.id,
            'amount_from': 1000.0,
            'amount_to': 5000.0,
            'graduated_commission_rate': 10.0,
        })
        rule3 = self.env['commission.graduated'].create({
            'commission_id': self.commission.id,
            'amount_from': 5000.0,
            'amount_to': 10000.0,
            'graduated_commission_rate': 15.0,
        })

        # Rules linked to commission should have sequences 1, 2, 3
        self.assertEqual(rule1.sequence, 1)
        self.assertEqual(rule2.sequence, 2)
        self.assertEqual(rule3.sequence, 3)

        # Standalone rule without a commission_id should have sequence 1
        rule_unlinked = self.env['commission.graduated'].create({
            'amount_from': 100.0,
            'amount_to': 200.0,
            'graduated_commission_rate': 2.0,
        })
        self.assertEqual(rule_unlinked.sequence, 1)

    def test__check_amounts(self):
        """Test _check_amounts constraint for valid and invalid amount ranges."""
        # Valid amount range should succeed
        rule = self.env['commission.graduated'].create({
            'commission_id': self.commission.id,
            'amount_from': 500.0,
            'amount_to': 1500.0,
            'graduated_commission_rate': 5.0,
        })
        self.assertTrue(rule.id)

        # Equal from and to amounts should succeed
        rule_equal = self.env['commission.graduated'].create({
            'commission_id': self.commission.id,
            'amount_from': 1000.0,
            'amount_to': 1000.0,
            'graduated_commission_rate': 5.0,
        })
        self.assertTrue(rule_equal.id)

        # Inverted amounts (amount_from > amount_to) should raise ValidationError
        with self.assertRaises(ValidationError):
            self.env['commission.graduated'].create({
                'commission_id': self.commission.id,
                'amount_from': 2000.0,
                'amount_to': 1000.0,
                'graduated_commission_rate': 5.0,
            })

        # Updating to an inverted amount should also raise ValidationError
        with self.assertRaises(ValidationError):
            rule.write({'amount_to': 400.0})
