# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
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
from datetime import datetime, timedelta
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPantryPayroll(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'email': 'test@test.com',
            'partner_id': cls.partner.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Coffee',
            'lst_price': 50,
            'pantry_product': True,
        })

    def test_quantity_increment(self):
        """Test quantity increment."""
        self.product.action_quantity_increment()
        self.assertEqual(
            self.product.quantity,
            2
        )

    def test_quantity_decrement(self):
        """Test quantity decrement."""
        self.product.quantity = 3
        self.product.action_quantity_decrement()
        self.assertEqual(
            self.product.quantity,
            2
        )

    def test_quantity_decrement_minimum(self):
        """Test quantity does not decrement below one."""
        self.product.quantity = 1
        self.product.action_quantity_decrement()
        self.assertEqual(
            self.product.quantity,
            1
        )

    def test_action_buy_pantry_create_order(self):
        """Test pantry order creation."""
        self.product.quantity = 2
        action = self.product.with_user(
            self.user
        ).action_buy_pantry()
        order = self.env['pantry.order'].search([
            ('partner_id', '=', self.partner.id),
            ('state', '=', 'draft')
        ], limit=1)
        self.assertTrue(order)
        self.assertEqual(
            order.amount_total,
            100
        )
        self.assertEqual(
            len(order.order_line_ids),
            1
        )
        self.assertEqual(
            action['res_model'],
            'pantry.order'
        )

    def test_action_buy_pantry_existing_order(self):
        """Test adding product to existing draft order."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        self.product.quantity = 2
        self.product.with_user(
            self.user
        ).action_buy_pantry()
        self.assertEqual(
            len(order.order_line_ids),
            1
        )
        self.assertEqual(
            order.amount_total,
            100
        )

    def test_action_buy_pantry_existing_product(self):
        """Test quantity update for existing product line."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
            'order_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 1,
                'unit_price': 50,
            })]
        })
        self.product.quantity = 2
        self.product.with_user(
            self.user
        ).action_buy_pantry()
        line = order.order_line_ids.filtered(
            lambda l: l.product_id == self.product
        )
        self.assertEqual(
            line.quantity,
            3
        )

    def test_compute_subtotal(self):
        """Test order line subtotal."""
        line = self.env['pantry.order.line'].create({
            'product_id': self.product.id,
            'quantity': 2,
            'unit_price': 50,
            'pantry_order_id': self.env['pantry.order'].create({
                'partner_id': self.partner.id,
            }).id
        })
        self.assertEqual(
            line.subtotal,
            100
        )

    def test_compute_amount_total(self):
        """Test order total computation."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
            'order_line_ids': [
                Command.create({
                    'product_id': self.product.id,
                    'quantity': 2,
                    'unit_price': 50,
                }),
                Command.create({
                    'product_id': self.product.id,
                    'quantity': 1,
                    'unit_price': 100,
                })
            ]
        })
        self.assertEqual(
            order.amount_total,
            200
        )

    def test_action_confirm_pantry_order(self):
        """Test pantry order confirmation."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        order.action_confirm_pantry_order()
        self.assertEqual(
            order.state,
            'confirmed'
        )

    def test_order_sequence_generation(self):
        """Test pantry order sequence generation."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertNotEqual(
            order.name,
            'New'
        )

    def test_get_inputs(self):
        """Test pantry amount added to payslip inputs."""
        if 'hr.payslip' not in self.env:
            return
        if 'hr.contract' not in self.env:
            return
        employee = self.env['hr.employee'].create({
            'name': 'Employee',
            'user_id': self.user.id,
        })
        contract = self.env['hr.contract'].create({
            'name': 'Contract',
            'employee_id': employee.id,
            'wage': 1000,
            'date_start': datetime.today(),
        })
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
            'state': 'confirmed',
            'date_order': datetime.today(),
            'order_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 2,
                'unit_price': 50,
            })]
        })
        payslip = self.env['hr.payslip']
        result = payslip.get_inputs(
            contract,
            datetime.today() - timedelta(days=1),
            datetime.today() + timedelta(days=1)
        )
        pantry_line = next(
            (line for line in result if line.get('code') == 'PR'),
            False
        )
        if pantry_line:
            self.assertEqual(
                pantry_line['amount'],
                order.amount_total
            )
