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
from types import SimpleNamespace
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.pantry_payroll.models.hr_payslip import HrPayslip


@tagged('post_install', '-at_install')
class TestPantryPayroll(TransactionCase):
    """Tests for pantry orders, pantry products and the payslip deduction."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Pantry Coffee',
            'lst_price': 10.0,
            'pantry_product': True,
        })
        cls.other_product = cls.env['product.product'].create({
            'name': 'Pantry Tea',
            'lst_price': 5.0,
            'pantry_product': True,
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Pantry Employee',
            'login': 'pantry_employee',
            'email': 'pantry.employee@example.com',
        })

    def _create_order(self, partner=None, lines=None):
        lines = lines if lines is not None else [(self.product, 2, 10.0)]
        return self.env['pantry.order'].create({
            'partner_id': (partner or self.user.partner_id).id,
            'order_line_ids': [fields.Command.create({
                'product_id': product.id,
                'quantity': qty,
                'unit_price': price,
            }) for product, qty, price in lines],
        })

    def test_order_sequence_and_defaults(self):
        """A new order gets a sequence, draft state and the order date."""
        order = self._create_order()
        self.assertTrue(order.name.startswith('PAO/'))
        self.assertEqual(order.state, 'draft')
        self.assertTrue(order.date_order)

    def test_order_totals(self):
        """Line subtotals and the order total are computed."""
        order = self._create_order(
            lines=[(self.product, 2, 10.0), (self.other_product, 3, 5.0)])
        self.assertEqual(order.order_line_ids[0].subtotal, 20.0)
        self.assertEqual(order.order_line_ids[1].subtotal, 15.0)
        self.assertEqual(order.amount_total, 35.0)
        order.order_line_ids[0].unit_price = 20.0
        self.assertEqual(order.amount_total, 55.0)

    def test_confirm_order(self):
        """Confirming an order changes its state."""
        order = self._create_order()
        order.action_confirm_pantry_order()
        self.assertEqual(order.state, 'confirmed')

    def test_quantity_buttons(self):
        """Quantity can be increased and never goes below one."""
        self.assertEqual(self.product.quantity, 1)
        self.product.action_quantity_increment()
        self.assertEqual(self.product.quantity, 2)
        self.product.action_quantity_decrement()
        self.assertEqual(self.product.quantity, 1)
        self.product.action_quantity_decrement()
        self.assertEqual(self.product.quantity, 1)

    def test_buy_pantry_creates_and_merges_order(self):
        """Buying creates a draft order, then adds to it on the next buy."""
        partner = self.env.user.partner_id
        self.env['pantry.order'].search([
            ('partner_id', '=', partner.id), ('state', '=', 'draft'),
        ]).unlink()
        self.product.quantity = 2
        action = self.product.action_buy_pantry()
        order = self.env['pantry.order'].browse(action['res_id'])
        self.assertEqual(action['res_model'], 'pantry.order')
        self.assertEqual(order.partner_id, partner)
        self.assertEqual(order.order_line_ids.quantity, 2)
        self.assertEqual(order.order_line_ids.unit_price, 10.0)
        self.assertEqual(self.product.quantity, 1)
        # Same product again: the existing line quantity is increased.
        self.product.quantity = 3
        self.product.action_buy_pantry()
        self.assertEqual(len(order.order_line_ids), 1)
        self.assertEqual(order.order_line_ids.quantity, 5)
        # Another product: a new line is added to the same draft order.
        self.other_product.action_buy_pantry()
        self.assertEqual(len(order.order_line_ids), 2)

    def test_pantry_product_flag(self):
        """The pantry flag is stored on the product template."""
        self.assertTrue(self.product.product_tmpl_id.pantry_product)
        plain = self.env['product.product'].create({'name': 'Plain'})
        self.assertFalse(plain.pantry_product)

    def test_payslip_pantry_input(self):
        """The pantry input of a payslip holds the orders of the period."""
        employee = self.env['hr.employee'].create({
            'name': 'Pantry Employee',
            'user_id': self.user.id,
        })
        contract = SimpleNamespace(id=1, employee_id=employee)
        self._create_order(lines=[(self.product, 2, 10.0)])
        self._create_order(lines=[(self.other_product, 1, 5.0)])
        payslip = self.env['hr.payslip']
        # The payroll module builds the list of inputs; only the pantry
        # input is relevant here, so the parent method is replaced.
        model_classes = type(payslip).__mro__
        parent = model_classes[model_classes.index(HrPayslip) + 1]
        today = fields.Date.context_today(self.env.user)
        past = fields.Date.subtract(today, days=10)
        with patch.object(
                parent, 'get_inputs', create=True,
                side_effect=lambda *a, **k: [
                    {'code': 'PR', 'name': 'Pantry', 'contract_id': 1},
                    {'code': 'OTHER', 'name': 'Other', 'contract_id': 1}]):
            inputs = payslip.get_inputs([contract], today, today)
            pantry = [line for line in inputs if line['code'] == 'PR']
            self.assertEqual(pantry[0]['amount'], 25.0)
            other = [line for line in inputs if line['code'] == 'OTHER']
            self.assertNotIn('amount', other[0])
            # Orders outside the period are not counted.
            inputs = payslip.get_inputs(
                [contract], past, fields.Date.subtract(today, days=5))
            pantry = [line for line in inputs if line['code'] == 'PR']
            self.assertEqual(pantry[0]['amount'], 0.0)
