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
Tests for the commission split workflow (crm.team.commission_split:
direct / equal) layered on top of the existing commission
engine (SaleOrder._update_commission_lines() / _get_commission_split_allocations()
in models/sale_order.py).

Covers: Direct, Equal (incl. rounding), no-team-members safety,
multiple commission calculation types, payment eligibility, returns,
and repeated processing not creating duplicate rows.
"""
from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCommissionSplit(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Split Customer'})

        cls.category = cls.env['product.category'].create({'name': 'Split Cat'})
        cls.product_a = cls.env['product.product'].create({
            'name': 'Split Product A',
            'list_price': 1000.0,
            'categ_id': cls.category.id,
        })

        cls.team = cls.env['crm.team'].create({'name': 'Split Sales Team'})

        cls.alice = cls.env['res.users'].create({
            'name': 'Alice', 'login': 'split_alice',
            'email': 'split_alice@example.com',
        })
        cls.bob = cls.env['res.users'].create({
            'name': 'Bob', 'login': 'split_bob',
            'email': 'split_bob@example.com',
        })
        cls.charlie = cls.env['res.users'].create({
            'name': 'Charlie', 'login': 'split_charlie',
            'email': 'split_charlie@example.com',
        })
        # Register alice/bob/charlie as formal crm.team.member records so
        # team.member_ids (a computed field derived from crm.team.member) is
        # populated correctly. Setting sale_team_id on res.users does NOT
        # create these membership records automatically.
        cls.env['crm.team.member'].create([
            {'crm_team_id': cls.team.id, 'user_id': cls.alice.id},
            {'crm_team_id': cls.team.id, 'user_id': cls.bob.id},
            {'crm_team_id': cls.team.id, 'user_id': cls.charlie.id},
        ])

    # ---- helpers ----------------------------------------------------

    def _make_plan(self, **vals):
        today = fields.Date.context_today(self.env.user)
        defaults = {
            'name': 'Split Plan',
            'date_from': today - timedelta(days=5),
            'date_to': today + timedelta(days=5),
            'type': 'revenue',
            'revenue_type': 'straight',
            'straight_commission_type': 'percentage',
            'straight_commission_rate': 10.0,
        }
        defaults.update(vals)
        return self.env['crm.commission'].create(defaults)

    def _make_order(self, user, qty=1, product=None, pay=True):
        product = product or self.product_a
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': user.id,
            'team_id': self.team.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': qty,
                'price_unit': product.list_price,
            })],
        })
        order.action_confirm()
        if pay:
            self._pay_order(order)
        return order

    def _pay_order(self, order):
        invoices = order._create_invoices()
        invoices.action_post()
        payment_register = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoices.ids,
        ).create({})
        payment_register._create_payments()
        return invoices

    def _amounts_by_user(self, order):
        result = {}
        for line in order.commission_line_ids.filtered(
                lambda ln: ln.commission_type == 'earned'):
            result[line.user_id] = result.get(line.user_id, 0.0) + line.amount
        return result

    # ---- Direct -------------------------------------------------------

    def test_direct_split_goes_entirely_to_order_salesperson(self):
        self.team.commission_split = 'direct'
        plan = self._make_plan(straight_commission_rate=90.0)  # 90% of 1000
        self.team.commission_id = plan.id
        order = self._make_order(self.alice)
        amounts = self._amounts_by_user(order)
        self.assertAlmostEqual(amounts.get(self.alice, 0.0), 900.0)
        self.assertAlmostEqual(amounts.get(self.bob, 0.0), 0.0)
        self.assertAlmostEqual(amounts.get(self.charlie, 0.0), 0.0)

    def test_default_commission_split_is_direct_for_backward_compatibility(self):
        # A brand-new team has no commission_split explicitly set by the
        # test -> must default/fall back to 'direct', preserving the
        # pre-split behaviour for any pre-existing data.
        self.assertEqual(self.team.commission_split, 'direct')

    # ---- Equal ----------------------------------------------------------

    def test_equal_split_divides_evenly_among_team_members(self):
        self.team.commission_split = 'equal'
        plan = self._make_plan(straight_commission_rate=90.0)  # 900
        self.team.commission_id = plan.id
        order = self._make_order(self.alice)
        amounts = self._amounts_by_user(order)
        self.assertAlmostEqual(amounts[self.alice], 300.0)
        self.assertAlmostEqual(amounts[self.bob], 300.0)
        self.assertAlmostEqual(amounts[self.charlie], 300.0)
        self.assertAlmostEqual(sum(amounts.values()), 900.0)

    def test_equal_split_rounding_sums_exactly(self):
        self.team.commission_split = 'equal'
        plan = self._make_plan(straight_commission_type='fixed',
                                straight_commission_fixed=100.0)
        self.team.commission_id = plan.id
        order = self._make_order(self.alice)
        amounts = self._amounts_by_user(order)
        self.assertEqual(len(amounts), 3)  # one allocation per member
        self.assertAlmostEqual(sum(amounts.values()), 100.0)
        # No allocation should be off by more than one cent from 100/3.
        for value in amounts.values():
            self.assertTrue(33.32 <= value <= 33.34)

    # ---- No team members ---------------------------------------------

    def test_no_team_members_falls_back_safely(self):
        empty_team = self.env['crm.team'].create({
            'name': 'Empty Team', 'commission_split': 'equal'})
        lone_user = self.env['res.users'].create({
            'name': 'Loner', 'login': 'split_loner',
            'email': 'split_loner@example.com',
        })
        # Use a fixed-amount plan so the expected value is deterministic
        # regardless of order revenue. Must also pass straight_commission_type
        # explicitly because _make_plan defaults to 'percentage'.
        plan = self._make_plan(straight_commission_type='fixed',
                               straight_commission_fixed=50.0)
        empty_team.commission_id = plan.id
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': lone_user.id,
            'team_id': empty_team.id,
            'order_line': [(0, 0, {
                'product_id': self.product_a.id,
                'product_uom_qty': 1,
                'price_unit': self.product_a.list_price,
            })],
        })
        order.action_confirm()
        self._pay_order(order)
        amounts = self._amounts_by_user(order)
        # Team has no configured members (crm.team.member_ids), but the
        # order's own salesperson is still folded in -> falls back to
        # a direct-style single allocation instead of crashing.
        self.assertAlmostEqual(amounts.get(lone_user, 0.0), 50.0)

    # ---- Multiple commission calculation types -------------------------

    def test_split_applies_to_product_wise_commission(self):
        self.team.commission_split = 'equal'
        plan = self._make_plan(type='product')
        self.env['commission.product'].create({
            'commission_id': plan.id,
            'product_id': self.product_a.id,
            'commission_amount_type': 'percentage',
            'percentage': 90.0,
            'amount': 1000.0,
        })
        self.team.commission_id = plan.id
        order = self._make_order(self.alice)  # 90% of 1000 = 900
        amounts = self._amounts_by_user(order)
        self.assertAlmostEqual(amounts[self.alice], 300.0)
        self.assertAlmostEqual(amounts[self.bob], 300.0)
        self.assertAlmostEqual(amounts[self.charlie], 300.0)

    def test_split_applies_to_graduated_commission(self):
        self.team.commission_split = 'equal'
        plan = self._make_plan(type='revenue', revenue_type='graduated')
        self.env['commission.graduated'].create({
            'commission_id': plan.id,
            'amount_from': 0.0,
            'amount_to': 0.0,
            'graduated_amount_type': 'percentage',
            'graduated_commission_rate': 90.0,
        })
        self.team.commission_id = plan.id
        order = self._make_order(self.alice)  # 90% of 1000 = 900
        amounts = self._amounts_by_user(order)
        self.assertAlmostEqual(amounts[self.alice], 300.0)
        self.assertAlmostEqual(amounts[self.bob], 300.0)
        self.assertAlmostEqual(amounts[self.charlie], 300.0)

    # ---- Payment eligibility is unaffected by splitting -----------------

    def test_split_only_applies_once_invoice_is_paid(self):
        self.team.commission_split = 'equal'
        plan = self._make_plan(straight_commission_fixed=90.0)
        self.team.commission_id = plan.id
        order = self._make_order(self.alice, pay=False)
        self.assertEqual(len(order.commission_line_ids), 0)
        self._pay_order(order)
        amounts = self._amounts_by_user(order)
        self.assertEqual(len(amounts), 3)

    # ---- Returns / clawback respect the original split -------------------

    def test_return_claws_back_according_to_original_split(self):
        self.team.commission_split = 'equal'
        plan = self._make_plan(straight_commission_type='percentage',
                                straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order = self._make_order(self.alice, qty=2)  # revenue 2000, comm 200
        amounts = self._amounts_by_user(order)
        for value in amounts.values():
            self.assertAlmostEqual(value, 200.0 / 3, delta=0.01)

        credit_note = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_a.id,
                'quantity': 1,
                'price_unit': 1000.0,
                'sale_line_ids': [(6, 0, order.order_line.ids)],
            })],
        })
        credit_note.action_post()

        returns = order.commission_line_ids.filtered(
            lambda ln: ln.commission_type == 'return')
        # One return line per original split allocation (Alice/Bob/Charlie),
        # each clawing back half of their own earned share.
        self.assertEqual(len(returns), 3)
        self.assertAlmostEqual(sum(returns.mapped('amount')), -100.0, delta=0.02)
        for user in (self.alice, self.bob, self.charlie):
            earned = order.commission_line_ids.filtered(
                lambda ln: ln.commission_type == 'earned' and ln.user_id == user)
            ret = returns.filtered(lambda ln: ln.user_id == user)
            self.assertAlmostEqual(ret.amount, -earned.amount / 2, delta=0.01)

    # ---- Plan source reference (team plan vs. salesperson plan) ------

    def test_plan_source_records_team_plan_when_team_has_one(self):
        team_plan = self._make_plan(name='Team Plan')
        self.team.commission_id = team_plan.id
        order = self._make_order(self.alice)
        self.assertTrue(order.commission_line_ids)
        self.assertTrue(
            all(line.plan_source == 'team'
                for line in order.commission_line_ids))

    def test_plan_source_records_user_plan_when_team_has_none(self):
        self.team.commission_split = 'direct'
        self.team.commission_id = False
        user_plan = self._make_plan(name='User Plan')
        self.alice.commission_id = user_plan.id
        order = self._make_order(self.alice)
        self.assertTrue(order.commission_line_ids)
        self.assertTrue(
            all(line.plan_source == 'user'
                for line in order.commission_line_ids))



    def test_repeated_processing_does_not_duplicate_split_records(self):
        self.team.commission_split = 'equal'
        plan = self._make_plan(straight_commission_type='fixed',
                               straight_commission_fixed=900.0)
        self.team.commission_id = plan.id
        order = self._make_order(self.alice)
        count_1 = len(order.commission_line_ids)
        order._update_commission_lines()
        order._update_commission_lines()
        count_2 = len(order.commission_line_ids)
        self.assertEqual(count_1, count_2)
        self.assertAlmostEqual(order.commission_amount, 900.0)
