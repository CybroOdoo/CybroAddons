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
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_billing')
class TestBillingMediumFixes(TransactionCase):
    """Regression tests for billing amounts, deletion guards, company scoping and access rights."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = fields.Date.today()
        cls.period_start = today.replace(day=1) - relativedelta(months=1)
        cls.period_end = today.replace(day=1) - relativedelta(days=1)

        cls.partner = cls.env['res.partner'].create({
            'name': 'Medium Fix Partner',
            'billing_mode': 'monthly_run',
        })
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Medium Fix Point',
            'partner_id': cls.partner.id,
        })
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Medium Fix Plastic', 'code': 'MFPLA', 'price': 1.0,
        })
        cls.ops_user = new_test_user(cls.env, login='wm_mf_ops', groups='wm_base.group_wm_ops_manager')
        cls.finance_user = new_test_user(cls.env, login='wm_mf_fin', groups='wm_base.group_wm_finance')
        cls.base_user = new_test_user(cls.env, login='wm_mf_user', groups='base.group_user')

    def _create_order(self, weight, day=5, partner=None, company=None, state='completed', hour=10):
        start = datetime.combine(self.period_start + relativedelta(days=day), time(hour, 0))
        vals = {
            'partner_id': (partner or self.partner).id,
            'collection_point_id': self.point.id,
            'scheduled_start': start,
            'scheduled_end': start + relativedelta(hours=1),
            'actual_start': start,
            'actual_end': start + relativedelta(hours=1),
            'state': state,
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': weight})],
        }
        if company:
            vals['company_id'] = company.id
        return self.env['wm.collection.order'].create(vals)

    def _run(self):
        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'partner_ids': [(6, 0, self.partner.ids)],
        })
        run.action_run_billing()
        return run

    def test_min_charge_line_bills_exact_total(self):
        """B-09: a minimum charge is billed as one unit at the exact amount."""
        self.env['wm.category.billing.rule'].create({
            'category_id': self.category.id,
            'partner_id': self.partner.id,
            'price': 1.0,
            'billing_basis': 'per_kg',
            'min_charge': 100.0,
        })
        self._create_order(7.0)
        run = self._run()
        invoice = run.invoice_ids
        self.assertEqual(len(invoice), 1)
        # Old code: round(100 / 7) = 14.29 x 7 kg = 100.03
        self.assertAlmostEqual(invoice.amount_untaxed, 100.0)
        line = invoice.invoice_line_ids.filtered(lambda ln: ln.display_type == 'product')
        self.assertEqual(line.quantity, 1.0)

    def test_per_kg_line_keeps_weight_and_rate(self):
        """B-09: without a minimum, the line is weight x rate."""
        self.env['wm.category.billing.rule'].create({
            'category_id': self.category.id,
            'partner_id': self.partner.id,
            'price': 0.35,
            'billing_basis': 'per_kg',
        })
        self._create_order(30.0)
        line = self._run().invoice_ids.invoice_line_ids.filtered(lambda ln: ln.display_type == 'product')
        self.assertEqual(line.quantity, 30.0)
        self.assertAlmostEqual(line.price_subtotal, 10.5)

    def test_zero_weight_fallback_not_billed(self):
        """B-08: a category with no weight left is not billed one unit at full price."""
        self._create_order(0.0)
        run = self._run()
        self.assertFalse(run.invoice_ids)

    def test_wizard_includes_orders_on_last_day(self):
        """B-10: orders completed during the last day of the range are fetched."""
        order = self._create_order(5.0, day=0, hour=15)
        wizard = self.env['wm.consolidated.billing.wizard'].create({
            'partner_id': self.partner.id,
            'date_from': self.period_start,
            'date_to': self.period_start,
        })
        self.assertIn(order, wizard._fetch_eligible_orders())

    def test_billed_run_and_consolidated_invoice_cannot_be_deleted(self):
        """B-11: deleting billed records would free their orders for re-billing."""
        self._create_order(10.0)
        run = self._run()
        self.assertEqual(run.state, 'done')
        with self.assertRaises(UserError):
            run.unlink()

        self.partner.billing_mode = 'consolidated'
        order = self._create_order(10.0, day=6)
        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'date_from': self.period_start,
            'date_to': self.period_end,
            'order_ids': [(6, 0, order.ids)],
        })
        consolidated.action_generate_invoice()
        with self.assertRaises(UserError):
            consolidated.unlink()
        self.assertEqual(order.consolidated_invoice_id, consolidated)

    def test_reset_consolidated_invoice_releases_events(self):
        """B-11: resetting a cancelled consolidated invoice frees its billable events."""
        event = self.env['wm.billable.event'].create({
            'partner_id': self.partner.id,
            'event_type': 'emergency_callout',
            'event_date': self.period_start + relativedelta(days=2),
            'price_unit': 50.0,
            'state': 'confirmed',
        })
        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'date_from': self.period_start,
            'date_to': self.period_end,
        })
        consolidated.action_generate_invoice()
        self.assertEqual(event.state, 'invoiced')
        consolidated.invoice_id.button_cancel()
        consolidated.action_reset_to_draft()
        self.assertEqual(event.state, 'confirmed')
        self.assertFalse(event.invoice_id)

    def test_monthly_cron_bills_per_company(self):
        """B-12: the cron run of a company never bills another company's orders."""
        company2 = self.env['res.company'].create({'name': 'Medium Fix Company 2'})
        self.env['account.journal'].create({
            'name': 'Customer Invoices 2',
            'code': 'INV2',
            'type': 'sale',
            'company_id': company2.id,
        })
        own_order = self._create_order(10.0)
        other_order = self._create_order(10.0, day=6, company=company2)
        self.env['wm.monthly.billing.run']._cron_run_monthly_billing()
        run = self.env['wm.monthly.billing.run'].search([
            ('period_start', '=', self.period_start),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        self.assertTrue(run)
        billed = run.line_ids.collection_order_ids
        self.assertIn(own_order, billed)
        self.assertNotIn(other_order, billed)

    def test_revenue_reports_resolve_all_pipelines(self):
        """B-14: cancelled orders are excluded and direct invoices count as invoiced."""
        cancelled = self._create_order(11.0, state='cancelled')
        direct = self._create_order(13.0, day=7)
        direct.action_create_invoice()
        self.env.flush_all()
        rows = self.env['wm.revenue.report'].search([('waste_category_id', '=', self.category.id)])
        self.assertAlmostEqual(sum(rows.mapped('weight_kg')), 13.0)
        self.assertTrue(cancelled)

        weight_rows = self.env['wm.weight.revenue.report'].search([('order_id', '=', direct.id)])
        self.assertTrue(weight_rows)
        self.assertEqual(sum(weight_rows.mapped('uninvoiced_order_count')), 0)

    def test_direct_invoice_requires_finance(self):
        """X-09: only billing staff can create a direct invoice from an order."""
        order = self._create_order(10.0)
        with self.assertRaises(AccessError):
            order.with_user(self.ops_user).action_create_invoice()
        self.assertFalse(order.direct_invoice_id)
        order.with_user(self.finance_user).action_create_invoice()
        self.assertTrue(order.direct_invoice_id)

    def test_billable_event_access(self):
        """X-10: dispatch staff read events; only billing staff create and invoice them."""
        Event = self.env['wm.billable.event']
        vals = {
            'partner_id': self.partner.id,
            'event_type': 'extra_pickup',
            'price_unit': 20.0,
        }
        with self.assertRaises(AccessError):
            Event.with_user(self.base_user).create(vals)
        with self.assertRaises(AccessError):
            self.env['wm.event.pricing.rule'].with_user(self.base_user).create({'event_type': 'extra_pickup'})
        event = Event.with_user(self.finance_user).create(vals)
        event.action_confirm()
        with self.assertRaises(AccessError):
            Event.with_user(self.base_user).search([('id', '=', event.id)])
        self.assertTrue(Event.with_user(self.ops_user).search([('id', '=', event.id)]))
        with self.assertRaises(AccessError):
            event.with_user(self.ops_user).action_create_invoice()
        event.with_user(self.finance_user).action_create_invoice()
        self.assertEqual(event.state, 'invoiced')

    def test_event_pricing_rule_scoped_to_company(self):
        """X-11: an event is never priced by another company's rule."""
        company2 = self.env['res.company'].create({'name': 'Medium Fix Company 3'})
        self.env['wm.event.pricing.rule'].create({
            'event_type': 'emergency_callout',
            'partner_id': self.partner.id,
            'price_unit': 999.0,
            'company_id': company2.id,
            'effective_date': self.period_start,
        })
        event = self.env['wm.billable.event'].create({
            'partner_id': self.partner.id,
            'event_type': 'emergency_callout',
        })
        self.assertNotEqual(event.price_unit, 999.0)

    def test_draft_contract_has_no_sign_url(self):
        """X-13: a draft contract never generates a signature request/link."""
        sla = self.env['wm.sla'].create({'name': 'MF SLA', 'terms_and_conditions': 'Terms'})
        contract = self.env['wm.partner.contract'].create({
            'name': 'WM-MF-DRAFT',
            'partner_id': self.partner.id,
            'sla_id': sla.id,
            'from_date': self.period_start,
            'to_date': self.period_end + relativedelta(years=1),
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 10.0,
            'max_weight': 500.0,
            'overweight_price': 5.0,
        })
        self.assertEqual(contract.state, 'draft')
        self.assertEqual(contract.get_portal_signature_url(), '')
        self.assertFalse(self.env['wm.signature.request'].search([
            ('reference_doc', '=', f'wm.partner.contract,{contract.id}'),
        ]))

    def test_ops_manager_reads_run_lines_and_slas(self):
        """V-14: operations managers can open run lines and SLA screens."""
        for model in ('wm.monthly.billing.run.line', 'wm.sla', 'wm.sla.line'):
            self.assertTrue(self.env[model].with_user(self.ops_user).has_access('read'), model)
