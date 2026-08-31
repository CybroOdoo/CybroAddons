# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged
from odoo.fields import Command
from odoo.addons.sale.tests.common import SaleCommon


@tagged('post_install', '-at_install')
class TestSaleOrderDiscountApproval(SaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._enable_discounts()

        cls.user_discount_controlled = cls.env['res.users'].create({
            'name': 'Discount Controlled User',
            'login': 'controlled_user',
            'email': 'controlled@example.com',
            'is_discount_control': True,
            'allow_discount': 10.0,
            'group_ids': [
                Command.link(cls.env.ref('sales_team.group_sale_salesman').id),
            ]
        })

        cls.user_normal = cls.env['res.users'].create({
            'name': 'Normal User',
            'login': 'normal_user',
            'email': 'normal@example.com',
            'is_discount_control': False,
            'group_ids': [
                Command.link(cls.env.ref('sales_team.group_sale_salesman').id),
            ]
        })

        cls.user_manager = cls.env['res.users'].create({
            'name': 'Discount Approval Manager',
            'login': 'manager_user',
            'email': 'manager@example.com',
            'group_ids': [
                Command.link(cls.env.ref('sales_team.group_sale_manager').id),
                Command.link(cls.env.ref('sale_order_discount_approval_odoo.sale_order_discount_approval_odoo_group_manager').id),
            ]
        })

        cls.discount_product = cls.env['product.product'].create({
            'name': 'Discount Product',
            'type': 'service',
        })
        cls.env.company.sale_discount_product_id = cls.discount_product

    def test_line_discount_within_limit(self):
        """Test that confirming a sale order with discount within user's allowed limit
        goes straight to 'sale' state without needing approval."""
        sale_order = self.env['sale.order'].with_user(self.user_discount_controlled).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                    'discount': 5.0,
                })
            ]
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')
        self.assertFalse(sale_order.approval_user_id)

    def test_line_discount_exceeds_limit(self):
        """Test that confirming a sale order with line discount exceeding limit
        puts it in 'waiting_for_approval' state, sends notifications, and is approveable by manager."""
        sale_order = self.env['sale.order'].with_user(self.user_discount_controlled).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                    'discount': 15.0,
                })
            ]
        })

        mail_count_before = self.env['mail.mail'].sudo().search_count([])

        sale_order.action_confirm()

        self.assertEqual(sale_order.state, 'waiting_for_approval')
        self.assertFalse(sale_order.approval_user_id)

        mail_count_after = self.env['mail.mail'].sudo().search_count([])
        self.assertTrue(mail_count_after > mail_count_before)

        sale_order.with_user(self.user_manager).action_waiting_approval()
        self.assertEqual(sale_order.state, 'sale')
        self.assertEqual(sale_order.approval_user_id, self.user_manager)

    def test_normal_user_no_discount_control(self):
        """Test that a user without discount control is not subject to limits."""
        sale_order = self.env['sale.order'].with_user(self.user_normal).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                    'discount': 50.0,
                })
            ]
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')

    def test_global_discount_within_limit(self):
        """Test that global discount percentage within the limit confirms normally."""
        sale_order = self.env['sale.order'].with_user(self.user_discount_controlled).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
                Command.create({
                    'product_id': self.discount_product.id,
                    'product_uom_qty': 1,
                    'price_unit': -5.0,
                })
            ]
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')

    def test_global_discount_exceeds_limit(self):
        """Test that global discount percentage exceeding the limit requires approval."""
        sale_order = self.env['sale.order'].with_user(self.user_discount_controlled).create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
                Command.create({
                    'product_id': self.discount_product.id,
                    'product_uom_qty': 1,
                    'price_unit': -15.0,
                })
            ]
        })
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'waiting_for_approval')
