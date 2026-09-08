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
from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'wm_billing')
class TestPipelineReconciliation(TransactionCase):
    """Unit tests verifying collection order invoice state transitions and billing pipeline."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        today = fields.Date.today()
        cls.period_start = today.replace(day=1) - relativedelta(months=1)
        cls.period_end = today.replace(day=1) - relativedelta(days=1)

        cls.partner_cons = cls.env['res.partner'].create({
            'name': 'Consolidated Billing Partner',
            'billing_mode': 'consolidated',
        })
        cls.partner_monthly = cls.env['res.partner'].create({
            'name': 'Monthly Run Partner',
            'billing_mode': 'monthly_run',
        })

        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Metal Waste',
            'code': 'METAL',
            'price': 10.0,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Scrap Metal Product',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
            'list_price': 10.0,
        })
        cls.point_cons = cls.env['wm.collection.point'].create({
            'name': 'Consolidated Point',
            'partner_id': cls.partner_cons.id,
        })
        cls.point_monthly = cls.env['wm.collection.point'].create({
            'name': 'Monthly Point',
            'partner_id': cls.partner_monthly.id,
        })

        dt = datetime.combine(cls.period_start + relativedelta(days=5), time(10, 0, 0))
        end_dt = datetime.combine(cls.period_start + relativedelta(days=5), time(11, 0, 0))

        cls.order_cons = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner_cons.id,
            'collection_point_id': cls.point_cons.id,
            'scheduled_start': dt,
            'scheduled_end': end_dt,
            'actual_start': dt,
            'actual_end': end_dt,
            'state': 'completed',
            'order_line_ids': [(0, 0, {
                'category_id': cls.category.id,
                'product_id': cls.product.id,
                'weight': 100.0,
            })]
        })

        cls.order_monthly = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner_monthly.id,
            'collection_point_id': cls.point_monthly.id,
            'scheduled_start': dt,
            'scheduled_end': end_dt,
            'actual_start': dt,
            'actual_end': end_dt,
            'state': 'completed',
            'order_line_ids': [(0, 0, {
                'category_id': cls.category.id,
                'product_id': cls.product.id,
                'weight': 150.0,
            })]
        })

    def test_back_to_back_crons_no_double_or_missed_billing(self):
        """
        Running both crons back-to-back results in zero double-billed orders
        and zero missed orders.
        """
        self.env['wm.consolidated.invoice']._cron_generate_monthly_invoices()
        self.env['wm.monthly.billing.run']._cron_run_monthly_billing()

        self.order_cons.invalidate_recordset()
        self.order_monthly.invalidate_recordset()

        # Check Consolidated Partner Order
        self.assertTrue(self.order_cons.consolidated_invoice_id, "Order for consolidated partner should be billed via consolidated invoice.")
        self.assertFalse(self.order_cons.billing_run_line_id, "Order for consolidated partner must not be picked up by monthly run.")
        self.assertTrue(self.order_cons.is_billed)

        # Check Monthly Run Partner Order
        self.assertTrue(self.order_monthly.billing_run_line_id, "Order for monthly run partner should be billed via monthly run.")
        self.assertFalse(self.order_monthly.consolidated_invoice_id, "Order for monthly run partner must not be picked up by consolidated invoice.")
        self.assertTrue(self.order_monthly.is_billed)

    def test_database_constraint_prevents_double_pipeline_claiming(self):
        """
        Assert that an order cannot have both consolidated_invoice_id and
        billing_run_line_id set.
        """
        cons_inv = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner_cons.id,
            'date_from': self.period_start,
            'date_to': self.period_end,
        })
        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
        })
        line = self.env['wm.monthly.billing.run.line'].create({
            'run_id': run.id,
            'partner_id': self.partner_cons.id,
        })

        with self.assertRaises(ValidationError):
            self.order_cons.write({
                'consolidated_invoice_id': cons_inv.id,
                'billing_run_line_id': line.id,
            })

    def test_shared_pricing_resolver(self):
        """
        Test canonical shared pricing resolver _get_billing_rule returns
        consistent rate rule.
        """
        self.env['wm.pricing.rule'].create({
            'name': 'Test Pricing Rule',
            'waste_category_id': self.category.id,
            'partner_id': self.partner_cons.id,
            'price_per_kg': 12.5,
            'min_weight': 50.0,
            'min_charge': 500.0,
        })

        rule = self.env['wm.collection.order']._get_billing_rule(self.category, self.partner_cons, fields.Date.today())
        self.assertIsNotNone(rule)
        self.assertEqual(rule.price, 12.5)
        self.assertEqual(rule.min_weight, 50.0)
        self.assertEqual(rule.min_charge, 500.0)
