# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

"""
Comprehensive tests for the live commission engine
(SaleOrder._update_commission_lines in models/sale_order.py).

Drop this file in commission_plan/tests/ as
test_sale_order_commission.py and add the import line
    from . import test_sale_order_commission
to tests/__init__.py.

Why this file exists
---------------------
The existing tests (test_commission_plan.py, test_crm_commission.py,
test_commission_product.py, test_commission_graduated.py,
test_commission_report.py) check field inheritance, onchange behaviour
and constraints -- but none of them ever confirm a sale.order and
check what lands in sale.order.commission. That is the one place all
the calculation branches actually run, so it's the part most likely
to have a bug that only shows up with real data.
"""
from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrderCommission(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})

        cls.category_parent = cls.env['product.category'].create(
            {'name': 'Hardware'})
        cls.category_child = cls.env['product.category'].create(
            {'name': 'Laptops', 'parent_id': cls.category_parent.id})

        cls.product_a = cls.env['product.product'].create({
            'name': 'Product A',
            'list_price': 1000.0,
            'categ_id': cls.category_child.id,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Product B (no rule)',
            'list_price': 500.0,
            'categ_id': cls.category_parent.id,
        })

        cls.team = cls.env['crm.team'].create({'name': 'Test Sales Team'})
        cls.salesperson = cls.env['res.users'].create({
            'name': 'Test Salesperson',
            'login': 'test_commission_salesperson',
            'email': 'test_commission_salesperson@example.com',
            'sale_team_id': cls.team.id,
        })

    # ---- helpers ----------------------------------------------------

    def _make_plan(self, **vals):
        today = fields.Date.context_today(self.env.user)
        defaults = {
            'name': 'Plan',
            'date_from': today - timedelta(days=5),
            'date_to': today + timedelta(days=5),
            'type': 'product',
        }
        defaults.update(vals)
        return self.env['crm.commission'].create(defaults)

    def _make_order(self, lines, user=None, team=None, date_order=None,
                     pay=True):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': (user or self.salesperson).id,
            'team_id': (team or self.team).id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'price_unit': product.list_price,
                }) for product, qty in lines
            ],
        })
        if date_order:
            order.date_order = date_order
        order.action_confirm()
        if pay:
            self._pay_order(order)
        return order

    def _pay_order(self, order):
        """Invoice the order, post it, and register a real payment through
        the standard wizard so the invoice goes through the actual
        reconciliation -> payment_state recompute path (the same path
        real-world payments take), rather than faking the field value.
        """
        invoices = order._create_invoices()
        invoices.action_post()
        payment_register = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoices.ids,
        ).create({})
        payment_register._create_payments()
        return invoices

    # ---- 1. product-wise, direct product match, percentage, under cap

    def test_product_rule_percentage_under_cap(self):
        plan = self._make_plan(type='product')
        self.env['commission.product'].create({
            'commission_id': plan.id,
            'product_id': self.product_a.id,
            'commission_amount_type': 'percentage',
            'percentage': 10.0,
            'amount': 1000.0,  # cap well above what will be earned
        })
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)])
        self.assertEqual(len(order.commission_line_ids), 1)
        self.assertAlmostEqual(order.commission_line_ids.amount, 100.0)  # 10% of 1000

    # ---- 2. product-wise, percentage capped by max amount

    def test_product_rule_percentage_capped(self):
        plan = self._make_plan(type='product')
        self.env['commission.product'].create({
            'commission_id': plan.id,
            'product_id': self.product_a.id,
            'commission_amount_type': 'percentage',
            'percentage': 50.0,   # 50% of 1000 = 500
            'amount': 200.0,      # cap at 200
        })
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)])
        self.assertAlmostEqual(order.commission_line_ids.amount, 200.0)

    # ---- 3. product-wise, fixed amount type (cap must NOT apply)

    def test_product_rule_fixed_amount_ignores_cap(self):
        plan = self._make_plan(type='product')
        self.env['commission.product'].create({
            'commission_id': plan.id,
            'product_id': self.product_a.id,
            'commission_amount_type': 'fixed',
            'fixed_amount': 300.0,
            'amount': 50.0,  # cap only meant for percentage type
        })
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)])
        self.assertAlmostEqual(order.commission_line_ids.amount, 300.0)

    # ---- 4. product-wise, category match including child category

    def test_product_rule_category_match(self):
        plan = self._make_plan(type='product')
        self.env['commission.product'].create({
            'commission_id': plan.id,
            'category_id': self.category_parent.id,  # parent category
            'commission_amount_type': 'percentage',
            'percentage': 5.0,
            'amount': 1000.0,
        })
        self.team.commission_id = plan.id
        # product_a is in the CHILD category -- must still match via child_of
        order = self._make_order([(self.product_a, 1)])
        self.assertEqual(len(order.commission_line_ids), 1)
        self.assertAlmostEqual(order.commission_line_ids.amount, 50.0)  # 5% of 1000

    # ---- 5. product not covered by any rule -> no commission

    def test_product_not_in_any_rule(self):
        plan = self._make_plan(type='product')
        self.env['commission.product'].create({
            'commission_id': plan.id,
            'product_id': self.product_a.id,
            'commission_amount_type': 'percentage',
            'percentage': 10.0,
            'amount': 1000.0,
        })
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_b, 1)])  # not in any rule
        self.assertEqual(len(order.commission_line_ids), 0)

    # ---- 6. revenue straight, percentage

    def test_revenue_straight_percentage(self):
        plan = self._make_plan(type='revenue', revenue_type='straight',
                                straight_commission_type='percentage',
                                straight_commission_rate=8.0)
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1), (self.product_b, 1)])
        self.assertAlmostEqual(order.commission_amount, 120.0)  # 8% of 1500

    # ---- 7. revenue straight, fixed

    def test_revenue_straight_fixed(self):
        plan = self._make_plan(type='revenue', revenue_type='straight',
                                straight_commission_type='fixed',
                                straight_commission_fixed=75.0)
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)])
        self.assertAlmostEqual(order.commission_amount, 75.0)

    # ---- 8. revenue graduated, correct bracket + inclusive upper bound

    def test_revenue_graduated_bracket_selection(self):
        plan = self._make_plan(type='revenue', revenue_type='graduated')
        self.env['commission.graduated'].create({
            'commission_id': plan.id,
            'amount_from': 0.0,
            'amount_to': 1000.0,
            'graduated_amount_type': 'percentage',
            'graduated_commission_rate': 5.0,
        })
        self.env['commission.graduated'].create({
            'commission_id': plan.id,
            'amount_from': 1000.0,
            'amount_to': 0.0,  # 0/false treated as "no upper bound"
            'graduated_amount_type': 'percentage',
            'graduated_commission_rate': 10.0,
        })
        self.team.commission_id = plan.id

        # revenue exactly 1000 -> boundary is inclusive on amount_to,
        # first bracket (0-1000) is checked first by sequence and matches
        order_low = self._make_order([(self.product_a, 1)])  # revenue 1000
        self.assertAlmostEqual(order_low.commission_amount, 50.0)  # 5% of 1000

        # revenue above 1000 -> should fall in the unlimited top bracket
        order_high = self._make_order(
            [(self.product_a, 1), (self.product_b, 1)])  # revenue 1500
        self.assertAlmostEqual(order_high.commission_amount, 150.0)  # 10% of 1500

    # ---- 9. team plan takes precedence over salesperson's own plan

    def test_team_plan_overrides_user_plan(self):
        team_plan = self._make_plan(
            name='Team Plan', type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        user_plan = self._make_plan(
            name='User Plan', type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=2.0)
        self.team.commission_id = team_plan.id
        self.salesperson.commission_id = user_plan.id
        order = self._make_order([(self.product_a, 1)])
        self.assertAlmostEqual(order.commission_amount, 100.0)  # team plan's 10%, not user's 2%

    # ---- 10. no team plan -> falls back to the salesperson's own plan

    def test_falls_back_to_user_plan_when_team_has_none(self):
        user_plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=4.0)
        self.salesperson.commission_id = user_plan.id
        self.team.commission_id = False
        order = self._make_order([(self.product_a, 1)])
        self.assertAlmostEqual(order.commission_amount, 40.0)

    # ---- 11. neither team nor user has a plan -> no commission at all

    def test_no_plan_anywhere_gives_no_commission(self):
        self.team.commission_id = False
        self.salesperson.commission_id = False
        order = self._make_order([(self.product_a, 1)])
        self.assertEqual(len(order.commission_line_ids), 0)
        self.assertEqual(order.commission_amount, 0.0)

    # ---- 12. order date outside the plan's validity window

    def test_order_date_before_plan_start(self):
        today = fields.Date.context_today(self.env.user)
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0,
            date_from=today + timedelta(days=1),
            date_to=today + timedelta(days=10))
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)], date_order=today)
        self.assertEqual(len(order.commission_line_ids), 0)

    def test_order_date_after_plan_end(self):
        today = fields.Date.context_today(self.env.user)
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0,
            date_from=today - timedelta(days=10),
            date_to=today - timedelta(days=1))
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)], date_order=today)
        self.assertEqual(len(order.commission_line_ids), 0)

    # ---- 13. order date exactly on the boundary -> inclusive, should count

    def test_order_date_on_plan_boundary_is_inclusive(self):
        today = fields.Date.context_today(self.env.user)
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0,
            date_from=today, date_to=today)
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)], date_order=today)
        self.assertEqual(len(order.commission_line_ids), 1)

    # ---- 14. plan set to revenue type but revenue_type sub-choice unset

    def test_revenue_type_unset_yields_no_commission(self):
        plan = self._make_plan(type='revenue')  # revenue_type left False
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)])
        self.assertEqual(len(order.commission_line_ids), 0)

    # ---- 15. idempotency: re-confirming / re-invoicing must not duplicate rows

    def test_recompute_is_idempotent_not_cumulative(self):
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)])
        self.assertEqual(len(order.commission_line_ids), 1)
        order._update_commission_lines()  # simulate a second trigger
        self.assertEqual(len(order.commission_line_ids), 1)
        self.assertAlmostEqual(order.commission_amount, 100.0)

    # ---- 16. an order with no lines can never be invoiced/paid, so it
    #          must never earn a commission, regardless of plan.

    def test_zero_revenue_order_straight_plan(self):
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.salesperson.id,
            'team_id': self.team.id,
        })
        order.action_confirm()
        self.assertEqual(len(order.commission_line_ids), 0)
        self.assertEqual(order.commission_amount, 0.0)

    # ---- 17. confirming an order does NOT earn commission until its
    #          invoice is actually paid.

    def test_no_commission_before_invoice_paid(self):
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)], pay=False)
        self.assertEqual(len(order.commission_line_ids), 0)
        self.assertEqual(order.commission_amount, 0.0)

        # Invoicing (but not paying) still must not create a commission.
        invoices = order._create_invoices()
        invoices.action_post()
        self.assertEqual(len(order.commission_line_ids), 0)

    # ---- 18. commission is created once the invoice is genuinely paid
    #          (through the real payment-registration/reconciliation path,
    #          not by faking the field), and removed again if the payment
    #          is unreconciled.

    def test_commission_created_on_payment_and_removed_if_unpaid(self):
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order = self._make_order([(self.product_a, 1)], pay=False)

        invoices = order._create_invoices()
        invoices.action_post()
        self.assertEqual(len(order.commission_line_ids), 0)

        payment_register = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoices.ids,
        ).create({})
        payment_register._create_payments()
        self.assertIn(invoices.payment_state, ('paid', 'in_payment'))
        self.assertEqual(len(order.commission_line_ids), 1)
        self.assertAlmostEqual(order.commission_amount, 100.0)  # 10% of 1000

        # Unreconciling the payment must take the commission away again.
        invoices.line_ids.filtered(
            lambda ln: ln.account_id.reconcile).remove_move_reconcile()
        self.assertNotIn(invoices.payment_state, ('paid', 'in_payment'))
        self.assertEqual(len(order.commission_line_ids), 0)
