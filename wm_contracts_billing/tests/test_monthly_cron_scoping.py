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
from datetime import datetime, time

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'wm_billing')
class TestMonthlyCronScoping(TransactionCase):
    """Unit tests verifying scheduled monthly billing cron job execution and filter scoping."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        today = fields.Date.today()
        cls.period_start = today.replace(day=1) - relativedelta(months=1)
        cls.period_end = today.replace(day=1) - relativedelta(days=1)

        # Partner 1: billing_mode = consolidated, no contract -> should be skipped by monthly billing cron
        cls.partner_cons_no_contract = cls.env['res.partner'].create({
            'name': 'Consolidated Partner No Contract',
            'billing_mode': 'consolidated',
        })

        # Partner 2: billing_mode = monthly_run, but 0 collection orders -> should produce 0 run/invoice records
        cls.partner_monthly_no_orders = cls.env['res.partner'].create({
            'name': 'Monthly Run Partner No Orders',
            'billing_mode': 'monthly_run',
        })

        # Partner 3: billing_mode = monthly_run, has active contract and valid completed collection order
        cls.partner_monthly_valid = cls.env['res.partner'].create({
            'name': 'Monthly Run Valid Partner',
            'billing_mode': 'monthly_run',
        })

        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Organic Waste Test Cron',
            'code': 'ORGCRON',
            'price': 15.0,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Compostable Product',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
            'list_price': 15.0,
        })
        cls.point_valid = cls.env['wm.collection.point'].create({
            'name': 'Valid Point',
            'partner_id': cls.partner_monthly_valid.id,
        })

        cls.sla = cls.env['wm.sla'].create({
            'name': 'Standard SLA Scoping',
            'terms_and_conditions': 'Standard terms and conditions text',
        })
        # Active contract for partner 3
        cls.contract = cls.env['wm.partner.contract'].create({
            'name': 'CTR/VALID/001',
            'partner_id': cls.partner_monthly_valid.id,
            'sla_id': cls.sla.id,
            'from_date': cls.period_start - relativedelta(days=10),
            'to_date': cls.period_end + relativedelta(days=30),
            'frequency': 'monthly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 500.0,
            'overweight_price': 5.0,
            'state': 'ongoing',
        })

        dt = datetime.combine(cls.period_start + relativedelta(days=5), time(10, 0, 0))
        end_dt = datetime.combine(cls.period_start + relativedelta(days=5), time(11, 0, 0))

        cls.order_valid = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner_monthly_valid.id,
            'collection_point_id': cls.point_valid.id,
            'scheduled_start': dt,
            'scheduled_end': end_dt,
            'actual_end': dt,
            'state': 'completed',
            'order_line_ids': [(0, 0, {
                'category_id': cls.category.id,
                'product_id': cls.product.id,
                'weight': 50.0,
                'price': 15.0,
            })],
        })

    def test_monthly_billing_cron_partner_scoping(self):
        """
        Monthly billing cron only processes monthly_run partners with valid
        orders and creates 0 run records if no orders match.
        """
        run_count_before = self.env['wm.monthly.billing.run'].search_count([])

        # Run monthly billing cron
        self.env['wm.monthly.billing.run']._cron_run_monthly_billing()

        runs = self.env['wm.monthly.billing.run'].search([('period_start', '=', self.period_start)])
        self.assertEqual(len(runs), 1, "Should create exactly 1 billing run for period.")

        run = runs[0]
        line_partners = run.line_ids.mapped('partner_id')
        self.assertIn(self.partner_monthly_valid, line_partners, "Valid monthly partner should be billed.")
        self.assertNotIn(self.partner_cons_no_contract, line_partners, "Consolidated partner should be skipped.")
        self.assertNotIn(self.partner_monthly_no_orders, line_partners, "Partner with 0 orders should not have lines.")

        # Test running cron again when all orders are already billed
        self.env['wm.monthly.billing.run']._cron_run_monthly_billing()
        run_count_after = self.env['wm.monthly.billing.run'].search_count([])
        self.assertEqual(run_count_after, run_count_before + 1, "No additional billing run record created when 0 billable orders remain.")
