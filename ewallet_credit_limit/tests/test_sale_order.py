# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestSaleOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrder, cls).setUpClass()
        # Setup Loyalty Program and Coupon Card
        cls.program = cls.env['loyalty.program'].create({
            'name': 'Test E-Wallet Program',
            'program_type': 'ewallet',
            'applies_on': 'future',
            'trigger': 'auto',
        })
        cls.card = cls.env['loyalty.card'].create({
            'program_id': cls.program.id,
            'points': 100.0,
            'limit': 100.0,
            'set_limit': True,
        })
        
        # Setup Partner and Product
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
            'type': 'consu',
        })

        # Setup Sale Order and Line
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.order_line = cls.env['sale.order.line'].create({
            'order_id': cls.sale_order.id,
            'product_id': cls.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 100.0,
            'coupon_id': cls.card.id,
            'points_cost': 15.0,
        })

    def test_action_confirm(self):
        """Test action_confirm updates coupon limit points successfully"""
        self.assertEqual(self.card.balance_limit_amount, 100.0)
        self.sale_order.action_confirm()
        # Should reduce by points_cost = 15.0
        self.assertEqual(self.card.balance_limit_amount, 85.0)

    def test_get_real_points_for_coupon_valid(self):
        """Test _get_real_points_for_coupon returns points correctly using balance limit amount"""
        self.card.write({
            'limit': 100.0,
            'set_limit': True,
        })

        # Calculate expected points:
        # points = 100.0 (since set_limit is True, uses balance_limit_amount)
        # Minus used points (order line points_cost is 15.0)
        # Expected points = 100.0 - 15.0 = 85.0
        points = self.sale_order._get_real_points_for_coupon(self.card)
        self.assertEqual(points, 85.0)

    def test_get_real_points_for_coupon_exceeded_error(self):
        """Test _get_real_points_for_coupon raises ValidationError if coupon balance limit is exceeded"""
        self.card.write({
            'limit': 0.0,
            'set_limit': True,
        })

        with self.assertRaises(ValidationError):
            self.sale_order._get_real_points_for_coupon(self.card)

