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
Tests for the return / credit-note commission clawback workflow added on
top of SaleOrder._update_commission_lines():
  - SaleOrder._create_return_commission_lines()
  - AccountMove._sync_commission_with_return() (posted/draft/cancel hooks)

Covers: full return of a straight-revenue-commission order, partial
return of a product-wise commission order, capping across several
credit notes, and un-posting a credit note removing the clawback again.
"""
from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrderCommissionReturn(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Return Customer'})

        cls.category = cls.env['product.category'].create({'name': 'Gadgets'})
        cls.product_a = cls.env['product.product'].create({
            'name': 'Return Product A',
            'list_price': 1000.0,
            'categ_id': cls.category.id,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Return Product B',
            'list_price': 500.0,
            'categ_id': cls.category.id,
        })

        cls.team = cls.env['crm.team'].create({'name': 'Return Sales Team'})
        cls.salesperson = cls.env['res.users'].create({
            'name': 'Return Salesperson',
            'login': 'test_commission_return_salesperson',
            'email': 'test_commission_return_salesperson@example.com',
            'sale_team_id': cls.team.id,
        })

    # ---- helpers ----------------------------------------------------

    def _make_plan(self, **vals):
        today = fields.Date.context_today(self.env.user)
        from datetime import timedelta
        defaults = {
            'name': 'Return Test Plan',
            'date_from': today - timedelta(days=5),
            'date_to': today + timedelta(days=5),
            'type': 'product',
        }
        defaults.update(vals)
        return self.env['crm.commission'].create(defaults)

    def _make_paid_order(self, lines):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.salesperson.id,
            'team_id': self.team.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'price_unit': product.list_price,
                }) for product, qty in lines
            ],
        })
        order.action_confirm()
        invoices = order._create_invoices()
        invoices.action_post()
        payment_register = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoices.ids,
        ).create({})
        payment_register._create_payments()
        return order, invoices

    def _credit_note(self, order, product, qty, price_unit):
        """Create and post a credit note crediting `qty` units of
        `product` back against `order`, linked via sale_line_ids the same
        way Odoo's own credit-note wizard links a refund back to the
        originating sale order line.
        """
        sale_line = order.order_line.filtered(
            lambda ln: ln.product_id == product)[:1]
        credit_note = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': qty,
                'price_unit': price_unit,
                'sale_line_ids': [(6, 0, sale_line.ids)],
            })],
        })
        credit_note.action_post()
        return credit_note

    # ---- 1. full return of a straight-revenue commission order fully
    #         cancels the earned commission

    def test_full_return_cancels_straight_commission(self):
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order, _invoices = self._make_paid_order([(self.product_a, 1)])
        self.assertAlmostEqual(order.commission_amount, 100.0)  # 10% of 1000

        self._credit_note(order, self.product_a, 1, 1000.0)

        earned = order.commission_line_ids.filtered(
            lambda ln: ln.commission_type == 'earned')
        returns = order.commission_line_ids.filtered(
            lambda ln: ln.commission_type == 'return')
        self.assertEqual(len(earned), 1)
        self.assertEqual(len(returns), 1)
        self.assertAlmostEqual(returns.amount, -100.0)
        self.assertAlmostEqual(order.commission_amount, 0.0)

    # ---- 2. partial return only claws back the prorated share

    def test_partial_return_prorates_commission(self):
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order, _invoices = self._make_paid_order([(self.product_a, 2)])
        self.assertAlmostEqual(order.commission_amount, 200.0)  # 10% of 2000

        # Return 1 of the 2 units -> half the revenue credited back.
        self._credit_note(order, self.product_a, 1, 1000.0)

        returns = order.commission_line_ids.filtered(
            lambda ln: ln.commission_type == 'return')
        self.assertAlmostEqual(returns.amount, -100.0)
        self.assertAlmostEqual(order.commission_amount, 100.0)

    # ---- 3. product-wise plan: return only claws back the rule the
    #         returned product belongs to, not unrelated product rules

    def test_product_wise_return_only_affects_matching_rule(self):
        plan = self._make_plan(type='product')
        self.env['commission.product'].create({
            'commission_id': plan.id,
            'product_id': self.product_a.id,
            'commission_amount_type': 'percentage',
            'percentage': 10.0,
            'amount': 1000.0,
        })
        self.env['commission.product'].create({
            'commission_id': plan.id,
            'product_id': self.product_b.id,
            'commission_amount_type': 'percentage',
            'percentage': 20.0,
            'amount': 1000.0,
        })
        self.team.commission_id = plan.id
        order, _invoices = self._make_paid_order(
            [(self.product_a, 1), (self.product_b, 1)])
        self.assertAlmostEqual(order.commission_amount, 200.0)  # 100 + 100

        self._credit_note(order, self.product_a, 1, 1000.0)

        earned_a = order.commission_line_ids.filtered(
            lambda ln: ln.commission_type == 'earned' and
            ln.product_id == self.product_a)
        earned_b = order.commission_line_ids.filtered(
            lambda ln: ln.commission_type == 'earned' and
            ln.product_id == self.product_b)
        returns = order.commission_line_ids.filtered(
            lambda ln: ln.commission_type == 'return')
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns.product_id, self.product_a)
        self.assertAlmostEqual(returns.amount, -100.0)
        self.assertAlmostEqual(order.commission_amount, 100.0)  # only b left
        self.assertAlmostEqual(earned_a.amount, 100.0)  # earned line itself untouched
        self.assertAlmostEqual(earned_b.amount, 100.0)

    # ---- 4. clawback across the order never exceeds what was earned,
    #         even if credit notes would otherwise imply more

    def test_return_amount_never_exceeds_earned_amount(self):
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order, _invoices = self._make_paid_order([(self.product_a, 1)])
        self.assertAlmostEqual(order.commission_amount, 100.0)

        # Two credit notes crediting the same unit back (e.g. a corrected
        # duplicate credit note) must still cap the clawback at -100.0,
        # never go further negative than what was actually earned.
        self._credit_note(order, self.product_a, 1, 1000.0)
        self._credit_note(order, self.product_a, 1, 1000.0)

        self.assertAlmostEqual(order.commission_amount, 0.0)
        self.assertGreaterEqual(order.commission_amount, -0.01)

    # ---- 5. un-posting (resetting to draft) a credit note removes its
    #         clawback again

    def test_resetting_credit_note_to_draft_removes_clawback(self):
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order, _invoices = self._make_paid_order([(self.product_a, 1)])

        credit_note = self._credit_note(order, self.product_a, 1, 1000.0)
        self.assertAlmostEqual(order.commission_amount, 0.0)

        credit_note.button_draft()
        self.assertAlmostEqual(order.commission_amount, 100.0)
        self.assertFalse(order.commission_line_ids.filtered(
            lambda ln: ln.commission_type == 'return'))

    # ---- 6. a credit note that fully reverses the invoice must NOT wipe
    #         out both the earned line and its return line. Odoo sets the
    #         reversed invoice's payment_state to 'reversed' (not 'paid'),
    #         which must still count as commission-eligible -- otherwise
    #         _update_commission_lines() unlinks everything up front and
    #         then bails out of recreating anything at all.

    def test_full_reversal_keeps_both_earned_and_return_lines(self):
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order, invoices = self._make_paid_order([(self.product_a, 1)])
        self.assertAlmostEqual(order.commission_amount, 100.0)

        credit_note = self._credit_note(order, self.product_a, 1, 1000.0)
        invoices.line_ids.filtered(
            lambda ln: ln.account_id.reconcile).remove_move_reconcile()
        (invoices + credit_note).line_ids.filtered(
            lambda ln: ln.account_id.reconcile and not ln.reconciled
        ).reconcile()

        self.assertEqual(invoices.payment_state, 'reversed')
        earned = order.commission_line_ids.filtered(
            lambda ln: ln.commission_type == 'earned')
        returns = order.commission_line_ids.filtered(
            lambda ln: ln.commission_type == 'return')
        self.assertEqual(len(earned), 1,
                          "earned commission line must survive a full "
                          "reversal, not be silently unlinked")
        self.assertEqual(len(returns), 1,
                          "return commission line must be created even "
                          "though the invoice is now 'reversed'")
        self.assertAlmostEqual(returns.amount, -100.0)
        self.assertAlmostEqual(order.commission_amount, 0.0)

    # ---- 7. no earned commission yet -> a credit note has nothing to
    #         claw back and creates no return line

    def test_return_with_no_earned_commission_is_a_noop(self):
        plan = self._make_plan(
            type='revenue', revenue_type='straight',
            straight_commission_type='percentage', straight_commission_rate=10.0)
        self.team.commission_id = plan.id
        order, invoices = self._make_paid_order([(self.product_a, 1)])
        # Unreconcile so the order is no longer commission-eligible.
        invoices.line_ids.filtered(
            lambda ln: ln.account_id.reconcile).remove_move_reconcile()
        self.assertEqual(len(order.commission_line_ids), 0)

        self._credit_note(order, self.product_a, 1, 1000.0)
        self.assertEqual(len(order.commission_line_ids), 0)
