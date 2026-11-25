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
"""Unit tests for the crm.commission model."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestCrmCommission(TransactionCase):
    """Test cases for crm.commission model functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'categ_id': cls.category.id,
            'list_price': 100.0,
        })

    def test__check_date(self):
        """Test _check_date constraint for valid and invalid date ranges."""
        # Valid date range should succeed
        commission = self.env['crm.commission'].create({
            'name': 'Valid Date Commission',
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
            'type': 'product',
        })
        self.assertTrue(commission.id)

        # Equal start and end date should also succeed
        commission_same_day = self.env['crm.commission'].create({
            'name': 'Same Day Commission',
            'date_from': '2026-06-01',
            'date_to': '2026-06-01',
            'type': 'product',
        })
        self.assertTrue(commission_same_day.id)

        # Inverted date range should raise ValidationError
        with self.assertRaises(ValidationError):
            self.env['crm.commission'].create({
                'name': 'Invalid Date Commission',
                'date_from': '2026-12-31',
                'date_to': '2026-01-01',
                'type': 'product',
            })

        # Updating to an invalid date range should also raise ValidationError
        with self.assertRaises(ValidationError):
            commission.write({'date_to': '2025-12-31'})

    def test__onchange_type(self):
        """Test _onchange_type clears incompatible fields upon type switch."""
        commission = self.env['crm.commission'].create({
            'name': 'Type Switch Commission',
            'date_from': '2026-01-01',
            'date_to': '2026-12-31',
            'type': 'product',
            'product_comm_ids': [(0, 0, {
                'product_id': self.product.id,
                'category_id': self.category.id,
                'percentage': 10.0,
                'amount': 500.0,
            })],
        })
        self.assertEqual(len(commission.product_comm_ids), 1)

        # Switch type to 'revenue' and trigger onchange
        commission.type = 'revenue'
        commission._onchange_type()
        self.assertFalse(commission.product_comm_ids)

        # Set revenue-specific fields
        commission.revenue_type = 'straight'
        commission.straight_commission_rate = 15.0
        commission.revenue_grd_comm_ids = [(0, 0, {
            'amount_from': 0.0,
            'amount_to': 1000.0,
            'graduated_commission_rate': 5.0,
        })]
        self.assertEqual(commission.revenue_type, 'straight')
        self.assertEqual(commission.straight_commission_rate, 15.0)
        self.assertEqual(len(commission.revenue_grd_comm_ids), 1)

        # Switch type back to 'product' and trigger onchange
        commission.type = 'product'
        commission._onchange_type()
        self.assertFalse(commission.revenue_type)
        self.assertFalse(commission.straight_commission_rate)
        self.assertFalse(commission.revenue_grd_comm_ids)
