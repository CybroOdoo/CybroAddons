#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import datetime, time

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_billing')
class TestBillingReviewFixes(TransactionCase):
    """Regression tests: allowance-covered run lines, per-contract
    subscriptions, order invoice links and direct invoice pricing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = fields.Date.today()
        cls.period_start = today.replace(day=1) - relativedelta(months=1)
        cls.period_end = today.replace(day=1) - relativedelta(days=1)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Review Fix Partner', 'billing_mode': 'monthly_run',
        })
        cls.other_partner = cls.env['res.partner'].create({
            'name': 'Review Fix Other Partner', 'billing_mode': 'monthly_run',
        })
        cls.point_a = cls.env['wm.collection.point'].create({'name': 'Review Point A', 'partner_id': cls.partner.id})
        cls.point_b = cls.env['wm.collection.point'].create({'name': 'Review Point B', 'partner_id': cls.partner.id})
        cls.other_point = cls.env['wm.collection.point'].create({
            'name': 'Review Other Point', 'partner_id': cls.other_partner.id})
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Review Fix Plastic', 'code': 'RVFPL', 'price': 1.0,
        })
        cls.sla = cls.env['wm.sla'].create({'name': 'Review SLA', 'terms_and_conditions': 'Terms'})
        cls.contract_a = cls._contract('WM-REVIEW-A', cls.point_a)
        cls.contract_b = cls._contract('WM-REVIEW-B', cls.point_b)

    @classmethod
    def _contract(cls, name, point):
        return cls.env['wm.partner.contract'].create({
            'name': name,
            'partner_id': cls.partner.id,
            'sla_id': cls.sla.id,
            'collection_point_ids': [(6, 0, point.ids)],
            'from_date': cls.period_start - relativedelta(months=1),
            'to_date': cls.period_end + relativedelta(years=1),
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'category_rate',
            'contract_line_ids': [(0, 0, {'category_id': cls.category.id, 'price': 2.0})],
            'state': 'ongoing',
        })

    def _subscription(self, contract, allowance):
        if 'wm.subscription' not in self.env:
            self.skipTest('wm_subscription not installed')
        plan = self.env['wm.subscription.plan'].create({
            'name': 'Review Plan %s' % contract.name, 'code': 'RV_%s' % contract.id,
            'recurring_price': 50.0, 'billing_cycle': 'monthly',
        })
        sub = self.env['wm.subscription'].create({
            'partner_id': contract.partner_id.id,
            'contract_id': contract.id,
            'plan_id': plan.id,
            'date_start': self.period_start,
            'included_monthly_weight_kg': allowance,
        })
        sub.write({'state': 'active'})
        return sub

    def _order(self, weight, contract=None, partner=None, point=None, day=5, period=True):
        base = self.period_start if period else fields.Date.today()
        start = datetime.combine(base + relativedelta(days=day if period else 0), time(10, 0))
        vals = {
            'partner_id': (partner or self.partner).id,
            'collection_point_id': (point or self.point_a).id,
            'scheduled_start': start,
            'scheduled_end': start + relativedelta(hours=1),
            'actual_start': start,
            'actual_end': start + relativedelta(hours=1),
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': weight})],
        }
        if contract is not None:
            vals['contract_id'] = contract.id
        order = self.env['wm.collection.order'].create(vals)
        # The contract is only kept while the order is a draft: complete it after
        order.sudo().with_context(programmatic_state_change=True).write({'state': 'completed'})
        return order

    def _run(self, partners):
        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'partner_ids': [(6, 0, partners.ids)],
        })
        run.action_run_billing()
        return run

    # ---- 2: orders fully covered by the subscription allowance ----------------
    def test_allowance_covered_orders_are_settled(self):
        """80 kg against a 100 kg allowance: no invoice, but the orders are billed."""
        self._subscription(self.contract_a, 100.0)
        orders = self._order(50.0, self.contract_a) | self._order(30.0, self.contract_a, day=6)
        self.assertEqual(orders.contract_id, self.contract_a)
        run = self._run(self.partner)

        self.assertEqual(run.state, 'done')
        self.assertFalse(run.invoice_ids)
        line = run.line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.state, 'billed')
        self.assertFalse(line.invoice_id)
        self.assertEqual(line.total_amount, 0.0)
        self.assertTrue(line.invoice_not_required)
        self.assertIn('subscription allowance', line.note)
        self.assertEqual(orders.billing_run_line_id, line)
        self.assertTrue(all(orders.mapped('is_billed')))
        self.assertFalse(orders.invoice_ids)

        billable = self.env['wm.collection.order']._get_billable_orders(
            self.partner, self.period_start, self.period_end)
        self.assertFalse(billable & orders)
        # A re-run does not bill them in full
        rerun = self._run(self.partner)
        self.assertFalse(rerun.invoice_ids)
        self.assertEqual(orders.billing_run_line_id, line)

    def test_allowance_covered_orders_not_unbilled_revenue(self):
        """The dashboard does not count settled (covered) orders as order revenue."""
        if 'wm.dashboard' not in self.env:
            self.skipTest('no dashboard')
        self._subscription(self.contract_a, 100.0)
        covered = self._order(80.0, self.contract_a)
        self._run(self.partner)
        unbilled = self._order(10.0, self.contract_a, period=False)
        domain = self.env['wm.dashboard']._get_order_revenue_exclusion_domain()
        found = self.env['wm.collection.order'].search(domain + [('id', 'in', (covered | unbilled).ids)])
        self.assertEqual(found, unbilled)

    # ---- 4: a contract's allowance only covers that contract ------------------
    def test_subscription_allowance_scoped_to_contract(self):
        """Contract B (no subscription) is billed in full; A's allowance is untouched."""
        self._subscription(self.contract_a, 500.0)
        order_a = self._order(200.0, self.contract_a)
        order_b = self._order(100.0, self.contract_b, point=self.point_b)
        run = self._run(self.partner)

        line_a = order_a.billing_run_line_id
        line_b = order_b.billing_run_line_id
        self.assertTrue(line_a and line_b)
        self.assertNotEqual(line_a, line_b)
        # A: 200 kg of the 500 kg allowance, nothing to invoice
        self.assertFalse(line_a.invoice_id)
        self.assertTrue(line_a.invoice_not_required)
        # B: 100 kg x 2.0, no allowance applied
        self.assertTrue(line_b.invoice_id)
        self.assertAlmostEqual(line_b.invoice_id.amount_untaxed, 200.0)
        self.assertFalse(line_b.invoice_not_required)
        self.assertEqual(run.invoice_ids, line_b.invoice_id)

    # ---- 5: an order only lists its own invoices ------------------------------
    def test_order_invoices_exclude_other_customers(self):
        """A run line without an invoice does not expose the run's other invoices."""
        self._subscription(self.contract_a, 100.0)
        covered = self._order(80.0, self.contract_a)
        other = self._order(40.0, partner=self.other_partner, point=self.other_point)
        run = self._run(self.partner | self.other_partner)

        self.assertTrue(other.billing_run_line_id.invoice_id)
        self.assertEqual(run.invoice_ids, other.billing_run_line_id.invoice_id)
        self.assertEqual(other.invoice_ids, other.billing_run_line_id.invoice_id)
        self.assertFalse(covered.invoice_ids)
        self.assertEqual(covered.invoice_count, 0)

    # ---- 6: the direct invoice bills the order lines as priced -----------------
    def test_direct_invoice_uses_manual_line_price(self):
        """A manual line price override is what gets invoiced."""
        order = self._order(40.0, partner=self.other_partner, point=self.other_point)
        line = order.order_line_ids
        self.assertEqual(line.price_basis, 'per_kg')
        line.price = 3.0
        self.assertAlmostEqual(order.total_amount, 120.0)
        order.action_create_invoice()
        invoice = order.direct_invoice_id
        self.assertAlmostEqual(invoice.amount_untaxed, 120.0)
        self.assertAlmostEqual(invoice.amount_untaxed, order.total_amount)
        inv_line = invoice.invoice_line_ids.filtered(lambda ln: ln.display_type == 'product')
        self.assertEqual(inv_line.price_unit, 3.0)
        self.assertEqual(inv_line.quantity, 40.0)

    def test_direct_invoice_minimum_only_at_rule_rate(self):
        """The rule minimum applies at the rule's own rate, not to a manual price."""
        self.env['wm.category.billing.rule'].create({
            'category_id': self.category.id,
            'partner_id': self.other_partner.id,
            'price': 1.0,
            'billing_basis': 'per_kg',
            'min_charge': 100.0,
        })
        at_rate = self._order(7.0, partner=self.other_partner, point=self.other_point)
        self.assertEqual(at_rate.order_line_ids.price, 1.0)
        at_rate.action_create_invoice()
        self.assertAlmostEqual(at_rate.direct_invoice_id.amount_untaxed, 100.0)

        manual = self._order(7.0, partner=self.other_partner, point=self.other_point, day=6)
        manual.order_line_ids.price = 20.0
        manual.action_create_invoice()
        self.assertAlmostEqual(manual.direct_invoice_id.amount_untaxed, 140.0)
        self.assertAlmostEqual(manual.direct_invoice_id.amount_untaxed, manual.total_amount)
