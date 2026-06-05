# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ahammed Harshad P(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from datetime import date, timedelta

class TestCommissionPlan(TransactionCase):

    def setUp(self):
        super(TestCommissionPlan, self).setUp()
        self.Salesperson = self.env['res.users'].create({
            'name': 'Test Salesperson',
            'login': 'test_salesperson',
            'email': 'test@example.com',
        })
        self.Product = self.env['product.product'].search([], limit=1)
        if not self.Product:
            self.Product = self.env['product.product'].create({
                'name': 'Test Product',
                'type': 'service',
                'list_price': 100.0,
            })
        self.Category = self.env['product.category'].create({
            'name': 'Test Category',
        })
        self.Product.categ_id = self.Category
        self.Partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })

    def test_straight_revenue_commission(self):
        """Test straight revenue commission (Percentage)"""
        commission_plan = self.env['crm.commission'].create({
            'name': 'Straight 10%',
            'type': 'revenue',
            'revenue_type': 'straight',
            'straight_commission_type': 'percentage',
            'straight_commission_rate': 10.0,
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today() + timedelta(days=30),
        })
        self.Salesperson.commission_id = commission_plan
        sale_order = self.env['sale.order'].create({
            'partner_id': self.Partner.id,
            'user_id': self.Salesperson.id,
            'order_line': [(0, 0, {
                'product_id': self.Product.id,
                'product_uom_qty': 10,
                'price_unit': 100.0,
            })]
        })
        sale_order.action_confirm()
        wizard = self.env['commission.report'].create({
            'salesperson_ids': [(4, self.Salesperson.id)],
            'date_from': date.today() - timedelta(days=1),
            'date_to': date.today() + timedelta(days=1),
        })
        user_commission_name = []
        user_commission_salesperson = []
        commission_list = []
        total_list = []
        user_sale_orders = self.env['sale.order'].search([('user_id', '=', self.Salesperson.id)])
        filtered_order_lines = user_sale_orders.mapped('order_line')
        filtered_order_lines_commission_total = sum(filtered_order_lines.mapped('price_subtotal'))
        wizard._calculate_straight_commission(
            commission_plan,
            filtered_order_lines_commission_total,
            commission_list,
            user_commission_name,
            user_commission_salesperson,
            total_list,
            self.Salesperson
        )
        self.assertEqual(filtered_order_lines_commission_total, 1000.0)
        self.assertEqual(commission_list[0], 100.0)

    def test_graduated_revenue_commission(self):
        """Test graduated revenue commission"""
        commission_plan = self.env['crm.commission'].create({
            'name': 'Graduated Plan',
            'type': 'revenue',
            'revenue_type': 'graduated',
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today() + timedelta(days=30),
            'revenue_grd_comm_ids': [(0, 0, {
                'amount_from': 0,
                'amount_to': 1000,
                'graduated_amount_type': 'percentage',
                'graduated_commission_rate': 5,
            }), (0, 0, {
                'amount_from': 1000,
                'amount_to': 5000,
                'graduated_amount_type': 'percentage',
                'graduated_commission_rate': 10,
            })]
        })
        self.Salesperson.commission_id = commission_plan
        sale_order_1 = self.env['sale.order'].create({
            'partner_id': self.Partner.id,
            'user_id': self.Salesperson.id,
            'order_line': [(0, 0, {
                'product_id': self.Product.id,
                'product_uom_qty': 5,
                'price_unit': 100.0,
            })]
        })
        sale_order_1.action_confirm()
        wizard = self.env['commission.report'].create({
            'salesperson_ids': [(4, self.Salesperson.id)],
        })
        commission_list = []
        user_commission_name = []
        user_commission_salesperson = []
        total_list = []
        filtered_order_lines_commission_total = 500.0
        rule = commission_plan.revenue_grd_comm_ids[0]
        wizard._calculate_graduated_commission(
            commission_list,
            user_commission_salesperson,
            total_list,
            self.Salesperson,
            commission_plan,
            rule,
            filtered_order_lines_commission_total,
            user_commission_name
        )
        self.assertEqual(commission_list[0], 25.0)

    def test_product_wise_commission(self):
        """Test product wise commission"""
        commission_plan = self.env['crm.commission'].create({
            'name': 'Product Wise Plan',
            'type': 'product',
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today() + timedelta(days=30),
            'product_comm_ids': [(0, 0, {
                'product_id': self.Product.id,
                'commission_amount_type': 'percentage',
                'percentage': 5.0,
                'amount': 1000.0,
            })]
        })
        self.Salesperson.commission_id = commission_plan
        sale_order = self.env['sale.order'].create({
            'partner_id': self.Partner.id,
            'user_id': self.Salesperson.id,
            'order_line': [(0, 0, {
                'product_id': self.Product.id,
                'product_uom_qty': 10,
                'price_unit': 100.0,
            })]
        })
        sale_order.action_confirm()
        wizard = self.env['commission.report'].create({
            'salesperson_ids': [(4, self.Salesperson.id)],
        })
        total_list = []
        commission_list = []
        user_commission_name = []
        user_commission_salesperson = []
        filtered_order_lines = sale_order.order_line
        wizard._calculate_product_commission(
            filtered_order_lines,
            total_list,
            commission_list,
            user_commission_salesperson,
            self.Salesperson,
            commission_plan,
            user_commission_name
        )
        self.assertEqual(commission_list[0], 50.0)
