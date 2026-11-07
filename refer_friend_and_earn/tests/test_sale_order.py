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
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrder(TransactionCase):
    """Test suite for sale.order referral discount fields."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Sale Order Referral Partner',
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def test_discount_applied(self):
        """Test setting discount_applied on sale order."""
        self.order.discount_applied = 12.5
        self.assertEqual(self.order.discount_applied, 12.5)

    def test_points_applied(self):
        """Test setting points_applied on sale order."""
        self.order.points_applied = 40.0
        self.assertEqual(self.order.points_applied, 40.0)
