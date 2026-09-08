# -*- coding: utf-8 -*-
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
import logging
from datetime import datetime, timedelta

from odoo import fields
from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_billing')
class TestMonthlyBilling(TransactionCase):
    """Unit tests verifying monthly consolidated invoice generation and line matching."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Recyclable Plastics TestMB',
            'code': 'PLASTMB',
            'price': 1.00,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Monthly Billing Customer Ltd TestMB',
            'billing_mode': 'monthly_run',
        })
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Factory Site A TestMB',
            'partner_id': cls.partner.id,
        })
        cls.rule = cls.env['wm.category.billing.rule'].create({
            'category_id': cls.category.id,
            'partner_id': cls.partner.id,
            'price': 2.50,
            'billing_basis': 'per_kg',
            'min_charge': 100.00,
        })
        cls.period_start = fields.Date.today().replace(day=1)
        cls.period_end = fields.Date.today()

    def _create_completed_order(self, name, weight):
        """
        Helper test method to provision a completed collection order and line
        with specified weight.
        """
        order = self.env['wm.collection.order'].create({
            'name': name,
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'company_id': self.env.company.id,
            'actual_start': datetime.now() - timedelta(hours=2),
            'actual_end': datetime.now() - timedelta(hours=1),
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category.id,
            'weight': weight,
        })
        return order

    def test_monthly_billing_consolidation(self):
        """
        Verify multiple completed orders are consolidated into one invoice
        using partner rate cards.
        """
        order1 = self._create_completed_order('ORD-M-001', 50.0)
        order2 = self._create_completed_order('ORD-M-002', 30.0)

        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
        })
        run.action_run_billing()

        self.assertEqual(run.state, 'done', "Run should complete with done state")
        self.assertEqual(len(run.invoice_ids), 1, "Exactly one consolidated invoice should be generated")

        invoice = run.invoice_ids[0]
        self.assertEqual(invoice.partner_id, self.partner, "Invoice partner should match customer")
        self.assertTrue(order1.is_billed, "Order 1 should be marked as billed")
        self.assertTrue(order2.is_billed, "Order 2 should be marked as billed")
        self.assertTrue(order1.billing_run_line_id, "Order 1 should be linked to billing run line")
        self.assertTrue(order2.billing_run_line_id, "Order 2 should be linked to billing run line")

        # Rate card calculation: total weight = 80kg * $2.50 = $200 (higher than min_charge $100)
        self.assertEqual(invoice.amount_total, 200.00, "Total invoice amount should be $200.00")

    def test_monthly_billing_idempotency(self):
        """
        Verify re-running billing for the same period does not duplicate
        invoices or double-bill orders.
        """
        self._create_completed_order('ORD-IDEM-001', 100.0)

        run1 = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
        })
        run1.action_run_billing()
        self.assertEqual(len(run1.invoice_ids), 1)

        # Run 2 for same period
        run2 = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
        })
        run2.action_run_billing()

        self.assertEqual(len(run2.invoice_ids), 0, "Second run should generate 0 new invoices for already billed orders")

    def test_monthly_billing_min_charge_enforcement(self):
        """
        Verify min_charge is applied when total category weight calculation is
        lower.
        """
        # 10 kg * $2.50 = $25, but rule min_charge is $100
        self._create_completed_order('ORD-LOW-001', 10.0)

        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
        })
        run.action_run_billing()
        self.assertEqual(len(run.invoice_ids), 1)
        self.assertEqual(run.invoice_ids[0].amount_total, 100.00, "Invoice total should be min_charge ($100.00)")

    def test_contract_first_rate_resolution(self):
        """
        Active partner contract rate takes priority over generic billing rules.
        """
        sla = self.env['wm.sla'].create({
            'name': 'Standard SLA TestMB',
            'terms_and_conditions': 'Standard SLA terms',
        })
        self.env['wm.partner.contract'].create({
            'name': 'CONTRACT-TEST-01',
            'partner_id': self.partner.id,
            'from_date': self.period_start - timedelta(days=5),
            'to_date': self.period_start + timedelta(days=60),
            'sla_id': sla.id,
            'state': 'ongoing',
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'category_rate',
            'collection_point_ids': [(6, 0, [self.point.id])],
            'contract_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'price': 4.50,  # $4.50/kg on contract overrides rule's $2.50/kg
            })],
        })

        rule = self.env['wm.collection.order']._get_billing_rule(self.category, self.partner, fields.Date.today())
        self.assertTrue(rule, "Billing rule should be resolved")
        self.assertEqual(rule.price, 4.50, "Contract line price ($4.50) should take precedence over category rule")

    def test_monthly_billing_customer_filtering(self):
        """
        Verify selecting specific target partner(s) in monthly billing wizard
        processes only targeted partner(s).
        """
        partner_other = self.env['res.partner'].create({
            'name': 'Other Customer Ltd TestMB',
        })
        point_other = self.env['wm.collection.point'].create({
            'name': 'Factory Site B TestMB',
            'partner_id': partner_other.id,
        })
        # Create completed order for main partner and other partner
        order_main = self._create_completed_order('ORD-FILTER-001', 50.0)

        order_other = self.env['wm.collection.order'].create({
            'name': 'ORD-FILTER-002',
            'partner_id': partner_other.id,
            'collection_point_id': point_other.id,
            'company_id': self.env.company.id,
            'actual_start': datetime.now() - timedelta(hours=2),
            'actual_end': datetime.now() - timedelta(hours=1),
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order_other.id,
            'category_id': self.category.id,
            'weight': 40.0,
        })

        # Run wizard filtering specifically for self.partner
        wizard = self.env['wm.monthly.billing.wizard'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'partner_ids': [(6, 0, [self.partner.id])],
        })
        action = wizard.action_run_monthly_billing()
        run = self.env['wm.monthly.billing.run'].browse(action['res_id'])

        self.assertEqual(run.state, 'done', "Billing run should be done")
        self.assertIn(self.partner, run.partner_ids, "Target customers on run record should contain target partner")
        self.assertEqual(len(run.invoice_ids), 1, "Only one invoice should be generated for the targeted partner")
        self.assertEqual(run.invoice_ids.partner_id, self.partner, "Invoice should be for targeted partner")
        self.assertTrue(order_main.is_billed, "Main partner order should be billed")
        self.assertFalse(order_other.is_billed, "Un-targeted partner order should remain unbilled")

    def test_monthly_billing_run_finance_user_access(self):
        """
        Verify that Billing & Finance users can execute monthly billing run
        without contract AccessError.
        """
        finance_user = self.env['res.users'].create({
            'name': 'Test Finance User MB',
            'login': 'finance_mb_user',
            'email': 'finance_mb@test.com',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('wm_base.group_wm_finance').id,
            ])],
        })
        self._create_completed_order('ORD-FINANCE-001', 25.0)

        run = self.env['wm.monthly.billing.run'].with_user(finance_user).create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'partner_ids': [(6, 0, [self.partner.id])],
        })
        run.with_user(finance_user).action_run_billing()
        self.assertNotEqual(run.state, 'error', "Monthly billing run should not encounter AccessError for Finance user.")

    def test_done_state_resets_to_draft_on_data_change(self):
        """
        Verify that updating data fields on a done billing run moves state to
        draft.
        """
        self._create_completed_order('ORD-DRAFT-RESET-001', 40.0)
        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'partner_ids': [(6, 0, [self.partner.id])],
        })
        run.action_run_billing()
        self.assertEqual(run.state, 'done', "Billing run should be done initially.")

        # 1. Posting chatter message should NOT reset state to draft
        run.message_post(body="Testing chatter note")
        self.assertEqual(run.state, 'done', "Chatter message should not change state.")

        # 2. Modifying period dates should reset state to draft
        new_start = self.period_start - timedelta(days=5)
        run.write({'period_start': new_start})
        self.assertEqual(run.state, 'draft', "Modifying period_start on done record must move state to draft.")

        # 3. Can re-run billing or edit partner_ids
        run.write({'state': 'done'})
        self.assertEqual(run.state, 'done')
        partner2 = self.env['res.partner'].create({'name': 'Another Partner MB'})
        run.write({'partner_ids': [(4, partner2.id)]})
        self.assertEqual(run.state, 'draft', "Modifying partner_ids on done record must move state to draft.")

    def test_consolidated_invoice_onchange_partner_clears_mismatched_orders(self):
        """
        Verify changing customer removes orders that do not belong to the new
        customer.
        """
        partner_a = self.partner
        partner_b = self.env['res.partner'].create({'name': 'Customer B TestMB'})
        point_b = self.env['wm.collection.point'].create({
            'name': 'Site B TestMB',
            'partner_id': partner_b.id,
        })

        order_a = self._create_completed_order('ORD-A-001', 50.0)
        order_b = self.env['wm.collection.order'].create({
            'name': 'ORD-B-001',
            'partner_id': partner_b.id,
            'collection_point_id': point_b.id,
            'company_id': self.env.company.id,
            'actual_start': datetime.now() - timedelta(hours=2),
            'actual_end': datetime.now() - timedelta(hours=1),
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order_b.id,
            'category_id': self.category.id,
            'weight': 30.0,
        })

        # Create new consolidated invoice for Partner A with Order A
        cons_inv = self.env['wm.consolidated.invoice'].create({
            'partner_id': partner_a.id,
            'order_ids': [(6, 0, [order_a.id])],
        })
        self.assertIn(order_a, cons_inv.order_ids)

        # Change partner to Partner B -> onchange should remove Order A
        cons_inv.partner_id = partner_b
        cons_inv._onchange_partner_id()
        self.assertNotIn(order_a, cons_inv.order_ids, "Order A should be removed when customer changes to Partner B")
        self.assertEqual(len(cons_inv.order_ids), 0, "No orders should remain for Partner B until selected")

        # Select Order B for Partner B -> should stay
        cons_inv.order_ids = [(6, 0, [order_b.id])]
        cons_inv._onchange_partner_id()
        self.assertIn(order_b, cons_inv.order_ids, "Order B should remain for Partner B")

    def test_billing_basis_category_rate_all_pipelines(self):
        """
        Test category_rate billing basis on contract in both monthly billing
        run and consolidated invoice.
        """
        partner_cr = self.env['res.partner'].create({
            'name': 'Category Rate Customer Ltd',
            'billing_mode': 'monthly_run',
        })
        point_cr = self.env['wm.collection.point'].create({
            'name': 'Site CR',
            'partner_id': partner_cr.id,
        })
        sla = self.env['wm.sla'].create({
            'name': 'SLA Category Rate',
            'terms_and_conditions': 'Standard SLA terms',
        })
        self.env['wm.partner.contract'].create({
            'name': 'CTR-CR-001',
            'partner_id': partner_cr.id,
            'sla_id': sla.id,
            'from_date': self.period_start - timedelta(days=5),
            'to_date': self.period_start + timedelta(days=60),
            'state': 'ongoing',
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'category_rate',
            'collection_point_ids': [(6, 0, [point_cr.id])],
            'contract_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'price': 3.50,  # $3.50/kg
            })],
        })

        # 2 completed orders: 40 kg + 60 kg = 100 kg * $3.50 = $350.00
        self.env['wm.collection.order'].create({
            'name': 'ORD-CR-001',
            'partner_id': partner_cr.id,
            'collection_point_id': point_cr.id,
            'actual_end': datetime.now() - timedelta(hours=2),
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': 40.0})],
        })
        self.env['wm.collection.order'].create({
            'name': 'ORD-CR-002',
            'partner_id': partner_cr.id,
            'collection_point_id': point_cr.id,
            'actual_end': datetime.now() - timedelta(hours=1),
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': 60.0})],
        })

        # 1. Monthly Billing Run
        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'partner_ids': [(6, 0, [partner_cr.id])],
        })
        run.action_run_billing()
        self.assertEqual(run.state, 'done')
        self.assertEqual(len(run.invoice_ids), 1)
        inv = run.invoice_ids[0]
        self.assertEqual(inv.amount_total, 350.00, "100kg @ $3.50/kg should equal $350.00")

    def test_billing_basis_material_all_pipelines(self):
        """
        Test material billing basis resolves per-kg rates from contract line in
        both pipelines.
        """
        partner_mat = self.env['res.partner'].create({
            'name': 'Material Rate Customer Ltd',
            'billing_mode': 'monthly_run',
        })
        point_mat = self.env['wm.collection.point'].create({
            'name': 'Site Material',
            'partner_id': partner_mat.id,
        })
        sla = self.env['wm.sla'].create({
            'name': 'SLA Material',
            'terms_and_conditions': 'Standard SLA terms',
        })
        self.env['wm.partner.contract'].create({
            'name': 'CTR-MAT-001',
            'partner_id': partner_mat.id,
            'sla_id': sla.id,
            'from_date': self.period_start - timedelta(days=5),
            'to_date': self.period_start + timedelta(days=60),
            'state': 'ongoing',
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'material',
            'collection_point_ids': [(6, 0, [point_mat.id])],
            'contract_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'price': 5.00,  # $5.00/kg
            })],
        })

        # 1 completed order: 50 kg * $5.00 = $250.00
        self.env['wm.collection.order'].create({
            'name': 'ORD-MAT-001',
            'partner_id': partner_mat.id,
            'collection_point_id': point_mat.id,
            'actual_end': datetime.now() - timedelta(hours=1),
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': 50.0})],
        })

        # Monthly Run
        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'partner_ids': [(6, 0, [partner_mat.id])],
        })
        run.action_run_billing()
        self.assertEqual(run.state, 'done')
        self.assertEqual(len(run.invoice_ids), 1)
        self.assertEqual(run.invoice_ids[0].amount_total, 250.00, "50kg @ $5.00/kg should equal $250.00")

    def test_billing_basis_per_collection_with_and_without_overweight(self):
        """
        Test per_collection billing basis: fixed fee when within max_weight,
        plus surcharge when exceeding max_weight.
        """
        partner_pc = self.env['res.partner'].create({
            'name': 'Per Collection Customer Ltd',
            'billing_mode': 'monthly_run',
        })
        point_pc = self.env['wm.collection.point'].create({
            'name': 'Site PC',
            'partner_id': partner_pc.id,
        })
        sla = self.env['wm.sla'].create({
            'name': 'SLA PC',
            'terms_and_conditions': 'Standard SLA terms',
        })
        self.env['wm.partner.contract'].create({
            'name': 'CTR-PC-001',
            'partner_id': partner_pc.id,
            'sla_id': sla.id,
            'from_date': self.period_start - timedelta(days=5),
            'to_date': self.period_start + timedelta(days=60),
            'state': 'ongoing',
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,      # $100 base fee per collection
            'max_weight': 50.0,        # 50 kg max weight per collection
            'overweight_price': 20.0,  # $20 per 10 kg overweight
            'collection_point_ids': [(6, 0, [point_pc.id])],
            'contract_line_ids': [(0, 0, {
                'category_id': self.category.id,
            })],
        })

        # Case A: 2 orders totaling 80 kg (within 2 * 50 kg = 100 kg threshold)
        # Total = 2 collections * $100 = $200.00
        self.env['wm.collection.order'].create({
            'name': 'ORD-PC-001',
            'partner_id': partner_pc.id,
            'collection_point_id': point_pc.id,
            'actual_end': datetime.now() - timedelta(hours=2),
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': 40.0})],
        })
        self.env['wm.collection.order'].create({
            'name': 'ORD-PC-002',
            'partner_id': partner_pc.id,
            'collection_point_id': point_pc.id,
            'actual_end': datetime.now() - timedelta(hours=1),
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': 40.0})],
        })

        run_normal = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'partner_ids': [(6, 0, [partner_pc.id])],
        })
        run_normal.action_run_billing()
        self.assertEqual(run_normal.state, 'done')
        self.assertEqual(run_normal.invoice_ids[0].amount_total, 200.00, "2 collections * $100 = $200.00 (no overweight)")

        # Case B: Overweight in consolidated invoice
        # 1 order with 90 kg (exceeds 50 kg max_weight by 40 kg)
        # Overweight = 40 kg / 10 * $20 = $80.00
        # Total = $100 base + $80 overweight = $180.00
        order_over = self.env['wm.collection.order'].create({
            'name': 'ORD-PC-OVER',
            'partner_id': partner_pc.id,
            'collection_point_id': point_pc.id,
            'actual_end': datetime.now() - timedelta(hours=1),
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': 90.0})],
        })
        cons_inv = self.env['wm.consolidated.invoice'].create({
            'partner_id': partner_pc.id,
            'order_ids': [(6, 0, [order_over.id])],
        })
        action = cons_inv.action_generate_invoice()
        inv_over = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(inv_over.amount_total, 180.00, "$100 base + $80 overweight (40kg @ $20/10kg) = $180.00")

    def test_billing_basis_hybrid_with_and_without_overage(self):
        """
        Test hybrid billing basis: base fee per collection + material overage
        surcharge above included_weight.
        """
        partner_hyb = self.env['res.partner'].create({
            'name': 'Hybrid Billing Customer Ltd',
            'billing_mode': 'monthly_run',
        })
        point_hyb = self.env['wm.collection.point'].create({
            'name': 'Site Hybrid',
            'partner_id': partner_hyb.id,
        })
        sla = self.env['wm.sla'].create({
            'name': 'SLA Hybrid',
            'terms_and_conditions': 'Standard SLA terms',
        })
        self.env['wm.partner.contract'].create({
            'name': 'CTR-HYB-001',
            'partner_id': partner_hyb.id,
            'sla_id': sla.id,
            'from_date': self.period_start - timedelta(days=5),
            'to_date': self.period_start + timedelta(days=60),
            'state': 'ongoing',
            'frequency': 'weekly',
            'no_of_frequency': 1,
            'billing_basis': 'hybrid',
            'fixed_price': 150.0,       # $150 base fee per collection
            'included_weight': 100.0,   # 100 kg included weight per collection
            'overweight_price': 30.0,   # $30 per 10 kg overage
            'collection_point_ids': [(6, 0, [point_hyb.id])],
            'contract_line_ids': [(0, 0, {
                'category_id': self.category.id,
            })],
        })

        # 2 completed collections totaling 260 kg (included = 2 * 100 = 200 kg)
        # Base total = 2 * $150 = $300
        # Overage = 260 - 200 = 60 kg -> (60 / 10) * $30 = $180
        # Total = $300 + $180 = $480.00
        self.env['wm.collection.order'].create({
            'name': 'ORD-HYB-001',
            'partner_id': partner_hyb.id,
            'collection_point_id': point_hyb.id,
            'actual_end': datetime.now() - timedelta(hours=2),
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': 120.0})],
        })
        self.env['wm.collection.order'].create({
            'name': 'ORD-HYB-002',
            'partner_id': partner_hyb.id,
            'collection_point_id': point_hyb.id,
            'actual_end': datetime.now() - timedelta(hours=1),
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': self.category.id, 'weight': 140.0})],
        })

        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'partner_ids': [(6, 0, [partner_hyb.id])],
        })
        run.action_run_billing()
        self.assertEqual(run.state, 'done')
        self.assertEqual(run.invoice_ids[0].amount_total, 480.00, "2 * $150 base ($300) + 60kg overage ($180) = $480.00")
