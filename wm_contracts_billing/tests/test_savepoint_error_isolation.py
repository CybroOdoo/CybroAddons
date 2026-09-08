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
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'wm_billing')
class TestSavepointErrorIsolation(TransactionCase):
    """Unit tests verifying SQL savepoint error isolation during monthly billing runs."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        today = fields.Date.today()
        cls.period_start = today.replace(day=1) - relativedelta(months=1)
        cls.period_end = today.replace(day=1) - relativedelta(days=1)

        # Partner 1 (will succeed)
        cls.partner_good = cls.env['res.partner'].create({
            'name': 'Good Monthly Partner',
            'billing_mode': 'monthly_run',
        })
        # Partner 2 (will fail during invoice creation due to patch)
        cls.partner_bad = cls.env['res.partner'].create({
            'name': 'Bad Monthly Partner',
            'billing_mode': 'monthly_run',
        })

        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Glass Waste Savepoint',
            'code': 'GLSSPT',
            'price': 20.0,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Glass Bottles Savepoint',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
            'list_price': 20.0,
        })

        cls.point_good = cls.env['wm.collection.point'].create({'name': 'Good Point', 'partner_id': cls.partner_good.id})
        cls.point_bad = cls.env['wm.collection.point'].create({'name': 'Bad Point', 'partner_id': cls.partner_bad.id})

        dt = datetime.combine(cls.period_start + relativedelta(days=5), time(10, 0, 0))
        end_dt = datetime.combine(cls.period_start + relativedelta(days=5), time(11, 0, 0))

        cls.order_good = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner_good.id,
            'collection_point_id': cls.point_good.id,
            'scheduled_start': dt,
            'scheduled_end': end_dt,
            'actual_end': dt,
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': cls.category.id, 'product_id': cls.product.id, 'weight': 100.0, 'price': 20.0})],
        })

        cls.order_bad = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner_bad.id,
            'collection_point_id': cls.point_bad.id,
            'scheduled_start': dt,
            'scheduled_end': end_dt,
            'actual_end': dt,
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': cls.category.id, 'product_id': cls.product.id, 'weight': 100.0, 'price': 20.0})],
        })

    def test_savepoint_error_isolation_on_monthly_run(self):
        """
        Monthly billing run with 1 failing line and 1 successful line marks
        failing line to state='error' and successful line to state='billed'
        without rolling back the successful line.
        """
        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'state': 'draft',
        })
        original_create = self.env['account.move'].create

        bad_partner_id = self.partner_bad.id

        def mock_create(*args, **kwargs):
            """
            Intercept record creation and simulate an unexpected database write
            exception during billing.
            """
            # In Odoo, create can be called as model.create(vals_list)
            vals_list = args[0] if args else kwargs.get('vals_list')
            if isinstance(vals_list, list):
                for vals in vals_list:
                    if vals.get('partner_id') == bad_partner_id:
                        raise Exception("Simulated invoice error for bad partner")
            elif isinstance(vals_list, dict) and vals_list.get('partner_id') == bad_partner_id:
                raise Exception("Simulated invoice error for bad partner")
            return original_create(*args, **kwargs)

        with patch.object(type(self.env['account.move']), 'create', side_effect=mock_create):
            run.action_run_billing()

        self.assertEqual(run.state, 'error')

        line_good = run.line_ids.filtered(lambda l: l.partner_id == self.partner_good)
        line_bad = run.line_ids.filtered(lambda l: l.partner_id == self.partner_bad)

        self.assertEqual(line_good.state, 'billed', "Good partner line should be state='billed'.")
        self.assertTrue(line_good.invoice_id, "Good partner line should have an invoice.")
        self.assertTrue(self.order_good.billing_run_line_id, "Good collection order should be linked to run line.")

        self.assertEqual(line_bad.state, 'error', "Bad partner line should be state='error'.")
        self.assertFalse(line_bad.invoice_id, "Bad partner line should have no invoice.")
        self.assertIn("Simulated invoice error", line_bad.error_message)
