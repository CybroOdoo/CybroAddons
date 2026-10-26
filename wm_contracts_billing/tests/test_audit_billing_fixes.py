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
from datetime import datetime, timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_billing')
class TestAuditBillingFixes(TransactionCase):
    """Regression tests for the billing audit findings (per-collection pricing,
    hybrid overage, contract currency, events in the monthly run, releases)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.partner = cls.env['res.partner'].create({'name': 'Audit Billing Customer', 'billing_mode': 'monthly_run'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Audit Billing Site', 'partner_id': cls.partner.id})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Audit Billing Waste', 'code': 'AUDBILL', 'price': 2.0})
        cls.sla = cls.env['wm.sla'].create({'name': 'Audit Billing SLA', 'terms_and_conditions': 'Terms'})

    def _contract(self, **vals):
        values = {
            'name': 'Audit Billing Contract',
            'partner_id': self.partner.id,
            'sla_id': self.sla.id,
            'from_date': self.today - timedelta(days=90),
            'to_date': self.today + timedelta(days=90),
            'frequency': 'monthly',
            'no_of_frequency': 1,
            'state': 'ongoing',
            'collection_point_ids': [(6, 0, self.point.ids)],
        }
        values.update(vals)
        return self.env['wm.partner.contract'].create(values)

    def _order(self, weight, contract=False):
        start = datetime.combine(self.today, datetime.min.time()) + timedelta(hours=8)
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'contract_id': contract.id if contract else False,
            'scheduled_start': start,
            'scheduled_end': start + timedelta(hours=1),
            'actual_start': start,
            'actual_end': start + timedelta(hours=1),
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': weight})],
        })
        # Created as a draft so the contract resolves, then completed as the workflow does
        order.sudo().with_context(programmatic_state_change=True).write({'state': 'completed'})
        return order

    def _run(self):
        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.today.replace(day=1), 'period_end': self.today + timedelta(days=1)})
        run.action_run_billing(partner_ids=self.partner.ids)
        return run

    # BUG-002
    def test_hybrid_contract_requires_and_bills_overage(self):
        with self.assertRaises(ValidationError):
            self._contract(billing_basis='hybrid', fixed_price=100.0, included_weight=100.0, overweight_price=0.0)
        contract = self._contract(billing_basis='hybrid', fixed_price=100.0, included_weight=100.0,
                                  overweight_price=10.0)
        rule = self.env['wm.collection.order']._get_billing_rule(
            self.category, self.partner, self.today, contract=contract)
        base, surcharge, *_rest = self.env['wm.collection.order']._compute_collection_fee(rule, 250.0, 1)
        self.assertAlmostEqual(base + surcharge, 250.0)

    # BUG-006
    def test_monthly_run_prices_each_collection_like_direct_invoices(self):
        contract = self._contract(billing_basis='per_collection', fixed_price=100.0, max_weight=500.0,
                                  overweight_price=10.0)
        order_a = self._order(700.0, contract)
        order_b = self._order(300.0, contract)
        direct = order_a.action_create_invoice()['res_id'], order_b.action_create_invoice()['res_id']
        direct_total = sum(self.env['account.move'].browse(direct).mapped('amount_untaxed'))
        # Reset the direct invoices so the same orders go through the monthly run
        for order in (order_a, order_b):
            order.sudo().write({'direct_invoice_id': False})
        run = self._run()
        self.assertEqual(run.state, 'done')
        self.assertAlmostEqual(sum(run.invoice_ids.mapped('amount_untaxed')), direct_total)
        self.assertAlmostEqual(direct_total, 400.0)

    # BUG-004
    def test_direct_invoice_uses_contract_currency(self):
        eur = self.env.ref('base.EUR')
        eur.active = True
        contract = self._contract(billing_basis='per_collection', fixed_price=100.0, max_weight=500.0,
                                  overweight_price=10.0, currency_id=eur.id)
        invoice = self.env['account.move'].browse(self._order(100.0, contract).action_create_invoice()['res_id'])
        self.assertEqual(invoice.currency_id, eur)
        self.assertAlmostEqual(invoice.amount_untaxed, 100.0)

    # BUG-005
    def test_monthly_run_invoices_billable_events(self):
        event = self.env['wm.billable.event'].create({
            'partner_id': self.partner.id, 'event_type': 'emergency_callout',
            'event_date': self.today, 'quantity': 1.0, 'price_unit': 75.0, 'state': 'confirmed'})
        run = self._run()
        event.invalidate_recordset()
        self.assertEqual(event.state, 'invoiced')
        self.assertIn(event.invoice_id, run.invoice_ids)
        self.assertEqual(event.invoice_line_id.move_id, event.invoice_id)

    # BUG-007 / BUG-008
    def test_zero_price_is_refused_and_cancelled_invoice_releases_orders(self):
        free_category = self.env['wm.waste.category'].create({'name': 'Audit Unpriced', 'code': 'AUDFREE', 'price': 0.0})
        order = self._order(10.0)
        order.order_line_ids.category_id = free_category
        run = self._run()
        self.assertEqual(run.state, 'error')
        self.assertFalse(order.billing_run_line_id, "An order priced at zero must stay unbilled")

        order.order_line_ids.category_id = self.category
        run2 = self._run()
        self.assertEqual(run2.state, 'done')
        self.assertTrue(order.billing_run_line_id)
        run2.invoice_ids.button_cancel()
        order.invalidate_recordset()
        self.assertFalse(order.billing_run_line_id, "Cancelling the invoice must release the order")

    def test_billable_event_rules(self):
        with self.assertRaises(ValidationError):
            self.env['wm.billable.event'].create({
                'partner_id': self.partner.id, 'event_type': 'extra_pickup', 'quantity': 0.0})

    def test_event_discount_reaches_amount_and_invoice(self):
        """A subscriber discount on an extra pickup lowers the amount and the invoice line."""
        event = self.env['wm.billable.event'].create({
            'partner_id': self.partner.id, 'event_type': 'extra_pickup',
            'quantity': 1.0, 'price_unit': 100.0, 'discount_pct': 20.0, 'state': 'confirmed',
        })
        self.assertAlmostEqual(event.amount, 80.0)
        event.action_create_invoice()
        line = event.invoice_line_id
        self.assertAlmostEqual(line.discount, 20.0)
        self.assertAlmostEqual(line.price_subtotal, 80.0)

    def test_confirmed_contract_prices_are_frozen(self):
        """Agreed prices cannot change once the contract is confirmed or ongoing."""
        from odoo.exceptions import UserError
        contract = self.env['wm.partner.contract'].search([('state', 'in', ('confirmed', 'ongoing'))], limit=1)
        if not contract:
            self.skipTest("no confirmed contract available")
        with self.assertRaises(UserError):
            contract.write({'fixed_price': contract.fixed_price + 1.0})
        # the sanctioned override still works (e.g. data migrations)
        contract.with_context(wm_contract_price_override=True).write({'fixed_price': contract.fixed_price})
